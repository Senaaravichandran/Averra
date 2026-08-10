"""Run Averra's local OpenCV camera check-in flow.

Usage: python camera.py
Press q to close the webcam. A recognized person is marked once per day.
"""

from datetime import datetime
from pathlib import Path
import sys
import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.averra import create_app
from backend.averra.db import get_db
from backend.averra.services.recognition import RecognitionService


def run() -> None:
    app = create_app()
    recognition = RecognitionService()
    if not recognition.available:
        raise SystemExit(f"Camera recognition is not available. {recognition.error}")
    if not recognition.labels:
        raise SystemExit("No recognizable profiles found in data/profiles/.")

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise SystemExit("Could not open the default webcam.")
    marked: set[str] = set()
    print(f"Averra camera ready with {len(recognition.labels)} profiles. Press q to close.")
    with app.app_context():
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            for match in recognition.identify(frame):
                top, right = match["box"]["top"], match["box"]["right"]
                bottom, left = match["box"]["bottom"], match["box"]["left"]
                known = match["name"] != "Unknown"
                color = (89, 190, 154) if known else (128, 127, 240)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, f"{match['name']}  {round(match['confidence'] * 100)}%", (left + 8, bottom - 9), cv2.FONT_HERSHEY_SIMPLEX, .55, (255, 255, 255), 1, cv2.LINE_AA)
                if known and match["name"] not in marked:
                    db = get_db(app.config["DATABASE_PATH"])
                    student = db.execute("SELECT id FROM students WHERE lower(name) = lower(?) AND status = 'active'", (match["name"],)).fetchone()
                    if student:
                        try:
                            db.execute("INSERT INTO attendance (student_id, attendance_date, check_in, method, confidence) VALUES (?, ?, ?, 'camera', ?)", (student["id"], datetime.now().date().isoformat(), datetime.now().strftime("%H:%M"), match["confidence"]))
                            db.commit()
                            print(f"{match['name']} present")
                        except Exception:
                            pass
                    db.close()
                    marked.add(match["name"])
            cv2.imshow("Averra · Camera check-in · press q to close", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
