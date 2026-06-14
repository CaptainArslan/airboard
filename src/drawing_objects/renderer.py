"""Render drawable objects onto frames and canvas buffers."""

import cv2
import numpy as np

from src.config import settings
from src.drawing import tools
from src.drawing_objects.arrow import Arrow
from src.drawing_objects.base import DrawableObject
from src.drawing_objects.circle import Circle
from src.drawing_objects.line import Line
from src.drawing_objects.rectangle import Rectangle


def render_objects(objects: list[DrawableObject], width: int, height: int) -> np.ndarray:
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    for obj in objects:
        if obj.visible:
            obj.render(canvas)
    return canvas


def blend_canvas(frame: np.ndarray, canvas: np.ndarray) -> np.ndarray:
    mask = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    has_drawing = mask > 0
    if not np.any(has_drawing):
        return frame
    blended = frame.copy()
    overlay = cv2.addWeighted(
        frame, 1 - settings.CANVAS_ALPHA,
        canvas, settings.CANVAS_ALPHA,
        0,
    )
    blended[has_drawing] = overlay[has_drawing]
    return blended


def render_object_overlay(frame: np.ndarray, obj: DrawableObject, preview: bool = False) -> None:
    """Draw a single object onto frame with canvas alpha blending (live preview layer)."""
    h, w = frame.shape[:2]
    layer = np.zeros((h, w, 3), dtype=np.uint8)
    if preview:
        _render_preview_object(layer, obj)
    else:
        obj.render(layer)
    mask = cv2.cvtColor(layer, cv2.COLOR_BGR2GRAY) > 0
    if not np.any(mask):
        return
    overlay = cv2.addWeighted(
        frame, 1 - settings.CANVAS_ALPHA,
        layer, settings.CANVAS_ALPHA,
        0,
    )
    frame[mask] = overlay[mask]


def _render_preview_object(layer: np.ndarray, obj: DrawableObject) -> None:
    """Render shape preview using preview color."""
    color = settings.PREVIEW_COLOR
    th = obj.thickness
    if isinstance(obj, Line):
        cv2.line(layer, obj.start_point, obj.end_point, color, th)
    elif isinstance(obj, Rectangle):
        cv2.rectangle(layer, obj.start_point, obj.end_point, color, th)
    elif isinstance(obj, Circle):
        cv2.circle(layer, obj.center_point, obj.radius, color, th)
    elif isinstance(obj, Arrow):
        cv2.arrowedLine(layer, obj.start_point, obj.end_point, color, th, tipLength=0.25)
    else:
        obj.render(layer)


def create_preview_shape(
    tool: str,
    start: tuple[int, int],
    end: tuple[int, int],
    color: tuple[int, int, int],
    thickness: int,
) -> DrawableObject | None:
    """Build a temporary shape object for live preview rendering."""
    if tool == tools.LINE:
        return Line(start_point=start, end_point=end, color=color, thickness=thickness)
    if tool == tools.RECTANGLE:
        return Rectangle(start_point=start, end_point=end, color=color, thickness=thickness)
    if tool == tools.CIRCLE:
        return Circle.from_points(start, end, color, thickness)
    if tool == tools.ARROW:
        return Arrow(start_point=start, end_point=end, color=color, thickness=thickness)
    return None


def compose_frame(
    camera_frame: np.ndarray,
    permanent_objects: list[DrawableObject],
    active_strokes: list[DrawableObject],
    shape_previews: list[DrawableObject],
) -> np.ndarray:
    """
    Compose display frame in order:
    1. Webcam
    2. Permanent canvas objects
    3. Active (uncommitted) freehand strokes
    4. Active shape previews
    """
    h, w = camera_frame.shape[:2]
    frame = camera_frame.copy()
    permanent_layer = render_objects(permanent_objects, w, h)
    frame = blend_canvas(frame, permanent_layer)
    for stroke in active_strokes:
        render_object_overlay(frame, stroke, preview=False)
    for shape in shape_previews:
        render_object_overlay(frame, shape, preview=True)
    return frame
