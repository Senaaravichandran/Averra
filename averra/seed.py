"""Idempotent demo data seeding."""

from datetime import date, datetime, timedelta
from pathlib import Path

from .db import get_db


STUDENTS = [
    ("Jobs", "jobs@northstar.edu", "AV-1042", "Computer Science", "JB"),
    ("Ratan Tata", "tata@northstar.edu", "AV-1043", "Product Design", "RT"),
    ("Sadmona", "sadmona@northstar.edu", "AV-1044", "Data Science", "SD"),
    ("Tesla", "tesla@northstar.edu", "AV-1045", "Computer Science", "TS"),
    ("Hari Babu", "haribabu@northstar.edu", "AV-1046", "Business Analytics", "HB"),
    ("Senaa", "senaa@northstar.edu", "AV-1047", "Product Design", "SN"),
    ("Shek", "shek@northstar.edu", "AV-1048", "Data Science", "SK"),
    ("Vnkat", "vnkat@northstar.edu", "AV-1049", "Computer Science", "VK"),
]


def seed_demo_data(database_path: str | Path) -> None:
    db = get_db(database_path)
    if db.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        db.executemany("INSERT INTO students (name, email, student_id, program, avatar) VALUES (?, ?, ?, ?, ?)", STUDENTS)
    if db.execute("SELECT COUNT(*) FROM schedules").fetchone()[0] == 0:
        today = date.today()
        db.executemany(
            "INSERT INTO schedules (title, room, starts_at, ends_at, accent) VALUES (?, ?, ?, ?, ?)",
            [
                ("Human Computer Interaction", "Studio 04", f"{today} 09:30", f"{today} 11:00", "coral"),
                ("Data Structures", "Lecture Hall A", f"{today} 11:30", f"{today} 13:00", "indigo"),
                ("Design Systems Lab", "Studio 02", f"{today} 14:00", f"{today} 15:30", "mint"),
                ("Product Strategy", "Room 201", f"{today} 16:00", f"{today} 17:30", "amber"),
            ],
        )
    if db.execute("SELECT COUNT(*) FROM attendance").fetchone()[0] == 0:
        students = db.execute("SELECT id FROM students ORDER BY id").fetchall()
        now = datetime.now()
        for offset in range(7):
            day = date.today() - timedelta(days=offset)
            for index, student in enumerate(students):
                if (index + offset) % 5 != 0:
                    db.execute(
                        "INSERT OR IGNORE INTO attendance (student_id, attendance_date, check_in, method, confidence) VALUES (?, ?, ?, 'camera', ?)",
                        (student["id"], day.isoformat(), (now - timedelta(days=offset, minutes=index * 3 + 8)).strftime("%H:%M"), round(0.93 - (index % 4) * 0.02, 2)),
                    )
    db.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", [("institution", "Northstar Institute"), ("timezone", "Asia/Calcutta"), ("recognition_threshold", "0.60")])
    db.commit()
    db.close()

