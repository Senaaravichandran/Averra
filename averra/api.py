"""Versioned JSON API for Averra."""

from datetime import date, datetime, timedelta, timezone
import csv
import io
import sqlite3

from flask import Blueprint, current_app, jsonify, request, send_file

from .auth import configured, login, require_admin
from .db import get_db, rows_to_dict
from .services.recognition import RecognitionService


api_bp = Blueprint("api", __name__)
recognition = RecognitionService()


def today_iso() -> str:
    return date.today().isoformat()


def error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def parse_date(value: str | None, fallback: date) -> date:
    try:
        return date.fromisoformat(value) if value else fallback
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format.") from exc


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "Averra", "environment": current_app.config["ENVIRONMENT"], "timestamp": datetime.now(timezone.utc).isoformat(), "recognition": recognition.status()})


@api_bp.get("/ready")
def ready():
    try:
        db = get_db(current_app.config["DATABASE_PATH"])
        db.execute("SELECT 1").fetchone()
        db.close()
        return jsonify({"status": "ready", "database": "ok"})
    except sqlite3.Error:
        return error("Database is unavailable.", 503)


@api_bp.route("/auth/session", methods=["GET", "POST", "DELETE"])
def auth_session():
    from flask import session
    if request.method == "GET":
        return jsonify({"authenticated": bool(session.get("admin_authenticated")), "configured": configured()})
    if request.method == "DELETE":
        session.clear()
        return jsonify({"authenticated": False})
    payload = request.get_json(silent=True) or {}
    if login(str(payload.get("email", "")).strip(), str(payload.get("password", ""))):
        return jsonify({"authenticated": True, "email": session.get("admin_email")})
    return error("Invalid credentials.", 401)


@api_bp.get("/overview")
def overview():
    db = get_db(current_app.config["DATABASE_PATH"])
    today = today_iso()
    total = db.execute("SELECT COUNT(*) AS count FROM students WHERE status = 'active'").fetchone()["count"]
    present = db.execute("SELECT COUNT(*) AS count FROM attendance WHERE attendance_date = ?", (today,)).fetchone()["count"]
    recent = db.execute("SELECT a.id, a.check_in, a.method, a.confidence, s.name, s.student_id AS roll_number, s.program, s.avatar FROM attendance a JOIN students s ON s.id = a.student_id WHERE a.attendance_date = ? ORDER BY a.check_in DESC LIMIT 8", (today,)).fetchall()
    schedule = db.execute("SELECT * FROM schedules WHERE starts_at LIKE ? ORDER BY starts_at", (f"{today}%",)).fetchall()
    week = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        count = db.execute("SELECT COUNT(*) AS count FROM attendance WHERE attendance_date = ?", (day.isoformat(),)).fetchone()["count"]
        week.append({"date": day.isoformat(), "label": day.strftime("%a"), "count": count})
    db.close()
    rate = round((present / total) * 100) if total else 0
    return jsonify({"date": today, "stats": {"present": present, "total": total, "rate": rate, "late": max(0, total - present)}, "recent": rows_to_dict(recent), "schedule": rows_to_dict(schedule), "week": week})


@api_bp.get("/students")
def students():
    db = get_db(current_app.config["DATABASE_PATH"])
    query = request.args.get("q", "").strip()
    sql = "SELECT s.*, (SELECT COUNT(*) FROM attendance a WHERE a.student_id = s.id) AS attendance_count FROM students s"
    params: list[str] = []
    if query:
        sql += " WHERE s.name LIKE ? OR s.email LIKE ? OR s.student_id LIKE ? OR s.program LIKE ?"
        params = [f"%{query}%"] * 4
    result = rows_to_dict(db.execute(sql + " ORDER BY s.name", params).fetchall())
    db.close()
    return jsonify(result)


@api_bp.post("/students")
@require_admin
def create_student():
    payload = request.get_json(silent=True) or {}
    required = ("name", "email", "student_id", "program")
    if any(not str(payload.get(key, "")).strip() for key in required):
        return error("Name, email, student ID, and program are required.")
    db = get_db(current_app.config["DATABASE_PATH"])
    try:
        cursor = db.execute("INSERT INTO students (name, email, student_id, program, avatar) VALUES (?, ?, ?, ?, ?)", tuple(str(payload[key]).strip() for key in required) + (payload.get("avatar", ""),))
        db.commit()
        student = db.execute("SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        db.close()
        return error("A student with that email or student ID already exists.", 409)
    db.close()
    return jsonify(dict(student)), 201


@api_bp.get("/attendance")
def attendance():
    try:
        selected_date = parse_date(request.args.get("date"), date.today()).isoformat()
    except ValueError as exc:
        return error(str(exc))
    db = get_db(current_app.config["DATABASE_PATH"])
    records = db.execute("SELECT a.id, a.student_id, a.attendance_date, a.check_in, a.method, a.confidence, s.name, s.student_id AS roll_number, s.program, s.avatar FROM attendance a JOIN students s ON s.id = a.student_id WHERE a.attendance_date = ? ORDER BY a.check_in DESC", (selected_date,)).fetchall()
    db.close()
    return jsonify({"date": selected_date, "records": rows_to_dict(records)})


@api_bp.post("/attendance")
@require_admin
def mark_attendance():
    payload = request.get_json(silent=True) or {}
    student_ref = payload.get("student_id")
    if not student_ref:
        return error("Choose a student to mark present.")
    method = payload.get("method", "manual")
    if method not in {"manual", "camera", "import"}:
        return error("Attendance method must be manual, camera, or import.")
    db = get_db(current_app.config["DATABASE_PATH"])
    student = db.execute("SELECT * FROM students WHERE id = ? AND status = 'active'", (student_ref,)).fetchone()
    if not student:
        db.close()
        return error("That active student could not be found.", 404)
    now = datetime.now()
    try:
        db.execute("INSERT INTO attendance (student_id, attendance_date, check_in, method, confidence) VALUES (?, ?, ?, ?, ?)", (student["id"], today_iso(), now.strftime("%H:%M"), method, payload.get("confidence")))
        db.commit()
        result = db.execute("SELECT a.*, s.name, s.student_id AS roll_number, s.program, s.avatar FROM attendance a JOIN students s ON s.id = a.student_id WHERE a.id = last_insert_rowid()").fetchone()
    except sqlite3.IntegrityError:
        db.close()
        return error("Attendance is already marked for this student today.", 409)
    db.close()
    return jsonify(dict(result)), 201


def report_data(start: date, end: date) -> dict:
    db = get_db(current_app.config["DATABASE_PATH"])
    rows = db.execute("SELECT s.id, s.name, s.student_id AS roll_number, s.program, COUNT(a.id) AS present_days FROM students s LEFT JOIN attendance a ON a.student_id = s.id AND a.attendance_date BETWEEN ? AND ? WHERE s.status = 'active' GROUP BY s.id ORDER BY present_days DESC, s.name", (start.isoformat(), end.isoformat())).fetchall()
    db.close()
    return {"start": start.isoformat(), "end": end.isoformat(), "rows": rows_to_dict(rows)}


@api_bp.get("/reports")
def reports():
    try:
        end = parse_date(request.args.get("end"), date.today())
        start = parse_date(request.args.get("start"), end - timedelta(days=6))
    except ValueError as exc:
        return error(str(exc))
    if start > end:
        return error("The report start date must be before the end date.")
    return jsonify(report_data(start, end))


@api_bp.get("/reports/export")
def export_report():
    try:
        end = parse_date(request.args.get("end"), date.today())
        start = parse_date(request.args.get("start"), end - timedelta(days=6))
    except ValueError as exc:
        return error(str(exc))
    if start > end:
        return error("The report start date must be before the end date.")
    report = report_data(start, end)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student", "Student ID", "Program", "Present days", "Period start", "Period end"])
    for row in report["rows"]:
        writer.writerow([row["name"], row["roll_number"], row["program"], row["present_days"], report["start"], report["end"]])
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name=f"averra-attendance-{report['end']}.csv")


@api_bp.get("/recognition/status")
def recognition_status():
    return jsonify(recognition.status())

