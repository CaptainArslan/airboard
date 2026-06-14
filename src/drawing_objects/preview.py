"""Shape preview rendering (non-committed)."""

import math

import cv2
import numpy as np

from src.config import settings
from src.drawing import tools


def draw_shape_preview(
    frame: np.ndarray,
    tool: str,
    start: tuple[int, int] | None,
    end: tuple[int, int] | None,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    if start is None or end is None:
        return
    preview_color = settings.PREVIEW_COLOR
    if tool == tools.LINE:
        cv2.line(frame, start, end, preview_color, thickness)
    elif tool == tools.RECTANGLE:
        cv2.rectangle(frame, start, end, preview_color, thickness)
    elif tool == tools.CIRCLE:
        radius = max(int(math.hypot(end[0] - start[0], end[1] - start[1])), 1)
        cv2.circle(frame, start, radius, preview_color, thickness)
    elif tool == tools.ARROW:
        cv2.arrowedLine(frame, start, end, preview_color, thickness, tipLength=0.25)
