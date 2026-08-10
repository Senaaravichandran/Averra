"""Optional OpenCV/face-recognition adapter used by the camera runner and API."""

from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class RecognitionService:
    def __init__(self, image_dir: str | Path | None = None):
        self.image_dir = Path(image_dir) if image_dir else PROJECT_ROOT / "data" / "profiles"
        self.encodings: list[Any] = []
        self.labels: list[str] = []
        self.available = False
        self.error = ""
        self._face_recognition = None
        try:
            import face_recognition

            self._face_recognition = face_recognition
            self.available = True
            self.reload()
        except ImportError as exc:
            self.error = f"Optional camera dependencies are unavailable: {exc.name}"

    def reload(self) -> int:
        if not self.available:
            return 0
        self.encodings.clear()
        self.labels.clear()
        aliases = {"tata": "Ratan Tata", "haribabu": "Hari Babu"}
        for path in sorted(self.image_dir.glob("*")):
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            try:
                image = self._face_recognition.load_image_file(path)
                encodings = self._face_recognition.face_encodings(image)
                if encodings:
                    self.encodings.append(encodings[0])
                    self.labels.append(aliases.get(path.stem.casefold(), path.stem.replace("_", " ").title()))
            except (OSError, ValueError):
                continue
        return len(self.labels)

    def status(self) -> dict[str, Any]:
        return {"available": self.available, "profiles": len(self.labels), "image_directory": str(self.image_dir), "error": self.error}

    def identify(self, frame: Any) -> list[dict[str, Any]]:
        if not self.available or not self.encodings:
            return []
        rgb_frame = frame[:, :, ::-1] if len(frame.shape) == 3 else frame
        locations = self._face_recognition.face_locations(rgb_frame, model="hog")
        encodings = self._face_recognition.face_encodings(rgb_frame, locations)
        matches = []
        for location, encoding in zip(locations, encodings):
            distances = self._face_recognition.face_distance(self.encodings, encoding)
            best_index = int(distances.argmin())
            distance = float(distances[best_index])
            top, right, bottom, left = location
            matches.append({"name": self.labels[best_index] if distance < 0.6 else "Unknown", "confidence": round(max(0, 1 - distance), 3), "box": {"top": top, "right": right, "bottom": bottom, "left": left}})
        return matches
