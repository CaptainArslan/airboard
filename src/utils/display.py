"""Display and monitor utilities."""

import cv2
import numpy as np


def get_primary_monitor_size() -> tuple[int, int]:
    """
    Return (width, height) of the primary monitor in pixels.
    Uses tkinter for cross-platform detection; falls back to 1920x1080.
    """
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        if width > 0 and height > 0:
            return width, height
    except Exception:
        pass
    return 1920, 1080


def scale_from_screen(
    ratio: float,
    screen_width: int,
    screen_height: int,
    *,
    axis: str = "min",
) -> int:
    """Convert a ratio (0–1) to pixels along width, height, or min dimension."""
    if axis == "width":
        return max(1, int(screen_width * ratio))
    if axis == "height":
        return max(1, int(screen_height * ratio))
    return max(1, int(min(screen_width, screen_height) * ratio))


def resize_with_aspect_ratio(
    frame: np.ndarray,
    target_width: int,
    target_height: int,
) -> np.ndarray:
    """Fit frame inside target size without stretching; pad with black bars."""
    height, width = frame.shape[:2]
    if width == 0 or height == 0:
        return np.zeros((target_height, target_width, 3), dtype=np.uint8)

    scale = min(target_width / width, target_height / height)
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    resized = cv2.resize(frame, (new_width, new_height))

    output = np.zeros((target_height, target_width, 3), dtype=frame.dtype)
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    output[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
    return output


def setup_windowed_window(window_name: str, width: int, height: int) -> None:
    """Create a resizable window at the given size (not fullscreen)."""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, width, height)


def set_fullscreen(window_name: str, enabled: bool, window_width: int, window_height: int) -> None:
    """Toggle between fullscreen and windowed mode."""
    if enabled:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    else:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, window_width, window_height)
