"""Averra attendance platform: web app and JSON API."""

from datetime import date, datetime, timedelta
from pathlib import Path
import csv
import io
import sqlite3

from flask import Flask, jsonify, render_template, request, send_file

from config import APP_NAME, SECRET_KEY
from database import get_db, init_db, rows_to_dict
from seed import seed
from services.recognition import RecognitionService


app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JSON_SORT_KEYS"] = False
recognition = RecognitionService()


def bootstrap() -> None:
    init_db()
    db = get_db()
    has_students = db.execute("SELECT 1 FROM students LIMIT 1").fetchone()
    db.close()
    if not has_students:
        seed()


def today_iso() -> str:
    return date.today().isoformat()


def api_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


@app.get("/")
def index():
    return render_template("index.html", app_name=APP_NAME)


@app.get("/api/overview")
def overview():
    db = get_db()
    today = today_iso()
    total = db.execute("SELECT COUNT(*) AS count FROM students WHERE status = 'active'").fetchone()["count"]
    present = db.execute("SELECT COUNT(*) AS count FROM attendance WHERE attendance_date = ?", (today,)).fetchone()["count"]
    recent = db.execute("""
        SELECT a.id, a.check_in, a.method, a.confidence, s.name, s.student_id AS roll_number,
               s.program, s.avatar
        FROM attendance a JOIN students s ON s.id = a.student_id
        WHERE a.attendance_date = ? ORDER BY a.check_in DESC LIMIT 8
    """, (today,)).fetchall()
    schedule = db.execute("SELECT * FROM schedules WHERE starts_at LIKE ? ORDER BY starts_at", (f"{today}%",)).fetchall()
    week = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        count = db.execute("SELECT COUNT(*) AS count FROM attendance WHERE attendance_date = ?", (day.isoformat(),)).fetchone()["count"]
        week.append({"date": day.isoformat(), "label": day.strftime("%a"), "count": count})
    db.close()
    rate = round((present / total) * 100) if total else 0
    return jsonify({"date": today, "stats": {"present": present, "total": total, "rate": rate, "late": max(0, total - present)}, "recent": rows_to_dict(recent), "schedule": rows_to_dict(schedule), "week": week})


@app.get("/api/students")
def students():
    db = get_db()
    query = request.args.get("q", "").strip()
    sql = "SELECT s.*, (SELECT COUNT(*) FROM attendance a WHERE a.student_id = s.id) AS attendance_count FROM students s"
    params: list[str] = []
    if query:
        sql += " WHERE s.name LIKE ? OR s.email LIKE ? OR s.student_id LIKE ? OR s.program LIKE ?"
        params = [f"%{query}%"] * 4
    sql += " ORDER BY s.name"
    result = rows_to_dict(db.execute(sql, params).fetchall())
    db.close()
    return jsonify(result)


@app.post("/api/students")
def create_student():
    payload = request.get_json(silent=True) or {}
    required = ("name", "email", "student_id", "program")
    if any(not str(payload.get(key, "")).strip() for key in required):
        return api_error("Name, email, student ID, and program are required.")
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO students (name, email, student_id, program, avatar) VALUES (?, ?, ?, ?, ?)", tuple(str(payload[key]).strip() for key in required) + (payload.get("avatar", ""),))
        db.commit()
        student = db.execute("SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        db.close()
        return api_error("A student with that email or student ID already exists.", 409)
    db.close()
    return jsonify(dict(student)), 201


@app.get("/api/attendance")
def attendance():
    selected_date = request.args.get("date", today_iso())
    db = get_db()
    records = db.execute("""
        SELECT a.id, a.student_id, a.attendance_date, a.check_in, a.method, a.confidence,
               s.name, s.student_id AS roll_number, s.program, s.avatar
        FROM attendance a JOIN students s ON s.id = a.student_id
        WHERE a.attendance_date = ? ORDER BY a.check_in DESC
    """, (selected_date,)).fetchall()
    db.close()
    return jsonify({"date": selected_date, "records": rows_to_dict(records)})


@app.post("/api/attendance")
def mark_attendance():
    payload = request.get_json(silent=True) or {}
    student_ref = payload.get("student_id")
    if not student_ref:
        return api_error("Choose a student to mark present.")
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ? AND status = 'active'", (student_ref,)).fetchone()
    if not student:
        db.close()
        return api_error("That active student could not be found.", 404)
    now = datetime.now()
    try:
        db.execute("INSERT INTO attendance (student_id, attendance_date, check_in, method, confidence) VALUES (?, ?, ?, ?, ?)", (student["id"], today_iso(), now.strftime("%H:%M"), payload.get("method", "manual"), payload.get("confidence")))
        db.commit()
        result = db.execute("SELECT a.*, s.name, s.student_id AS roll_number, s.program, s.avatar FROM attendance a JOIN students s ON s.id = a.student_id WHERE a.id = last_insert_rowid()").fetchone()
    except sqlite3.IntegrityError:
        db.close()
        return api_error("Attendance is already marked for this student today.", 409)
    db.close()
    return jsonify(dict(result)), 201


@app.get("/api/reports")
def reports():
    end = date.fromisoformat(request.args.get("end", today_iso()))
    start = date.fromisoformat(request.args.get("start", (end - timedelta(days=6)).isoformat()))
    db = get_db()
    rows = db.execute("""
        SELECT s.id, s.name, s.student_id AS roll_number, s.program,
               COUNT(a.id) AS present_days
        FROM students s LEFT JOIN attendance a ON a.student_id = s.id
            AND a.attendance_date BETWEEN ? AND ?
        WHERE s.status = 'active' GROUP BY s.id ORDER BY present_days DESC, s.name
    """, (start.isoformat(), end.isoformat())).fetchall()
    db.close()
    return jsonify({"start": start.isoformat(), "end": end.isoformat(), "rows": rows_to_dict(rows)})


@app.get("/api/reports/export")
def export_report():
    report = reports().get_json()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student", "Student ID", "Program", "Present days", "Period start", "Period end"])
    for row in report["rows"]:
        writer.writerow([row["name"], row["roll_number"], row["program"], row["present_days"], report["start"], report["end"]])
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name=f"averra-attendance-{report['end']}.csv")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": APP_NAME, "timestamp": datetime.utcnow().isoformat() + "Z", "recognition": recognition.status()})


@app.get("/api/recognition/status")
def recognition_status():
    return jsonify(recognition.status())


bootstrap()


if __name__ == "__main__":
    app.run(debug=True, port=5050)
