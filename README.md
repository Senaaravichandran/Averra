# Averra

**Attendance, with clarity.**

Averra is a focused attendance workspace for modern classrooms and teams. It combines a calm operations dashboard, persistent attendance records, roster management, reporting, and an optional local OpenCV + `face_recognition` camera flow that marks a person once per day.

## What’s inside

- Responsive dashboard with attendance pulse, daily schedule, live check-in feed, and insight cards.
- Student directory with search and validated profile creation.
- Manual attendance marking with duplicate protection per day.
- Camera check-in page with browser permission flow and a local recognition runner.
- SQLite-backed reports with date ranges and CSV export.
- Health and recognition status endpoints.
- Automated API tests for the important user journeys.

## Run locally

Python 3.10+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Open [http://127.0.0.1:5050](http://127.0.0.1:5050).

The first run creates `instance/averra.sqlite3` and seeds a Northstar Institute demo workspace. Set `AVERRA_DATABASE` and `AVERRA_SECRET` for a different database location or deployment secret.

## Camera recognition

Install the optional native packages from `requirements-camera.txt`, then place one clear profile photo per person in `students/`. The filename becomes the recognition label. Start the local OpenCV loop with:

```powershell
python camera.py
```

The camera opens and stays active until `q` is pressed. Recognized faces receive a rectangle and confidence label; known people are written to Averra’s SQLite attendance log with a `camera` method. If the native packages are unavailable, the web product stays usable in manual/demo mode and exposes the reason at `/api/recognition/status`.

## Verify

```powershell
pytest
```

## Project map

```text
app.py                 Flask routes and JSON API
camera.py              OpenCV camera runner (press q to quit)
database.py            SQLite schema and connections
seed.py                Safe demo workspace seeding
services/recognition.py Optional face-recognition adapter
templates/index.html   Responsive Averra application shell
static/css/            Design system and camera surface styles
static/js/app.js       API-connected browser interactions
tests/                 API and workflow coverage
```

## Production notes

For a production deployment, place Averra behind HTTPS, set a long random `AVERRA_SECRET`, use a managed database if multiple application instances are needed, and configure authentication/role-based access before exposing the API publicly. The current build is intentionally self-contained and ideal for a local institution, a pilot, or a strong base for those next operational layers.
