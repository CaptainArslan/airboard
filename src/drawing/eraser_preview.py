"""Professional eraser circle preview rendering."""

import cv2
import numpy as np

# Theme-aligned eraser preview (BGR)
_ERASER_OUTLINE = (68, 68, 239)   # #EF4444
_ERASER_FILL = (40, 40, 120)      # subtle red tint
_ERASER_INNER = (255, 255, 255)   # inner highlight


def draw_eraser_preview(
    frame: np.ndarray,
    cx: int,
    cy: int,
    radius: int,
    fill_alpha: float = 0.12,
) -> None:
    """Draw anti-aliased eraser circle outline with subtle fill."""
    if radius < 1:
        return
    overlay = frame.copy()
    cv2.circle(overlay, (cx, cy), radius, _ERASER_FILL, -1, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, fill_alpha, frame, 1 - fill_alpha, 0, frame)
    cv2.circle(frame, (cx, cy), radius, _ERASER_OUTLINE, 2, lineType=cv2.LINE_AA)
    inner_r = max(1, radius - 4)
    cv2.circle(frame, (cx, cy), inner_r, _ERASER_OUTLINE, 1, lineType=cv2.LINE_AA)
