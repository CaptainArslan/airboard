import cv2

from src.config import settings


class CameraManager:
    """Handles webcam capture lifecycle."""

    def __init__(self):
        self._cap = cv2.VideoCapture(settings.CAMERA_INDEX)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Could not open webcam at index {settings.CAMERA_INDEX}. "
                "Check camera permissions and that no other app is using it."
            )

    def read_raw(self):
        """Read one mirrored BGR frame at native resolution."""
        success, frame = self._cap.read()
        if not success:
            return None
        return cv2.flip(frame, 1)

    def release(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None
