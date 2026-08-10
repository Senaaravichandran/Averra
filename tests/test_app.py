from pathlib import Path

import pytest

import database
from app import app
from database import get_db, init_db
from seed import seed


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "test.sqlite3")
    init_db()
    seed()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_health_reports_service_and_recognition(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Averra"
    assert "recognition" in payload
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_app_shell_and_pwa_assets_are_available(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/manifest.json").get_json()["short_name"] == "Averra"
    assert client.get("/static/sw.js").status_code == 200


def test_overview_contains_seeded_workspace(client):
    response = client.get("/api/overview")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["stats"]["total"] == 8
    assert len(payload["week"]) == 7
    assert payload["schedule"]


def test_student_creation_and_duplicate_protection(client):
    student = {"name": "Neha Rao", "email": "neha@northstar.edu", "student_id": "AV-1099", "program": "Economics"}
    response = client.post("/api/students", json=student)
    assert response.status_code == 201
    assert response.get_json()["name"] == "Neha Rao"

    duplicate = client.post("/api/students", json=student)
    assert duplicate.status_code == 409


def test_attendance_is_idempotent_per_day(client):
    first = client.post("/api/attendance", json={"student_id": 1, "method": "manual"})
    assert first.status_code == 201
    assert first.get_json()["method"] == "manual"

    second = client.post("/api/attendance", json={"student_id": 1, "method": "manual"})
    assert second.status_code == 409

    records = client.get("/api/attendance").get_json()["records"]
    assert any(record["student_id"] == 1 for record in records)


def test_api_rejects_invalid_dates_and_methods(client):
    assert client.get("/api/attendance?date=tomorrow").status_code == 400
    assert client.get("/api/reports?start=2026-08-10&end=2026-08-01").status_code == 400
    invalid_method = client.post("/api/attendance", json={"student_id": 2, "method": "telepathy"})
    assert invalid_method.status_code == 400


def test_report_and_csv_export(client):
    report = client.get("/api/reports").get_json()
    assert report["start"] < report["end"]
    assert len(report["rows"]) == 8

    export = client.get("/api/reports/export")
    assert export.status_code == 200
    assert export.mimetype == "text/csv"
    assert b"Student,Student ID" in export.data
