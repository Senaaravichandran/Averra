"""Optional face-recognition adapter.

The product remains useful without native CV dependencies. When OpenCV and
face_recognition are installed, this adapter loads images from students/ and
exposes a small, testable recognition surface for the local camera runner.
"""

from pathlib import Path
from typing import Any


class RecognitionService:
    def __init__(self, image_dir: str | Path = "students"):
        self.image_dir = Path(image_dir)
        self.encodings: list[Any] = []
        self.labels: list[str] = []
        self.available = False
        self.error = ""
        self._face_recognition = None
        self._cv2 = None
        try:
            import cv2
            import face_recognition

            self._cv2 = cv2
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
        extensions = {".jpg", ".jpeg", ".png", ".webp"}
        for path in sorted(self.image_dir.glob("*")):
            if path.suffix.lower() not in extensions:
                continue
            try:
                image = self._face_recognition.load_image_file(path)
                encodings = self._face_recognition.face_encodings(image)
                if encodings:
                    self.encodings.append(encodings[0])
                    profile_labels = {"tata": "Ratan Tata", "haribabu": "Hari Babu"}
                    self.labels.append(profile_labels.get(path.stem.casefold(), path.stem.replace("_", " ").title()))
            except (OSError, ValueError):
                continue
        return len(self.labels)

    def status(self) -> dict[str, Any]:
        return {"available": self.available, "profiles": len(self.labels), "image_directory": str(self.image_dir), "error": self.error}

    def identify(self, frame: Any) -> list[dict[str, Any]]:
        """Return matched faces for an RGB or BGR frame.

        This method deliberately returns serializable geometry and confidence
        values so it can later be used by a browser camera endpoint as well.
        """
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
            label = self.labels[best_index] if distance < 0.6 else "Unknown"
            top, right, bottom, left = location
            matches.append({"name": label, "confidence": round(max(0, 1 - distance), 3), "box": {"top": top, "right": right, "bottom": bottom, "left": left}})
        return matches
