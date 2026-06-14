"""Object-based drawing model."""

from src.drawing_objects.arrow import Arrow
from src.drawing_objects.base import DrawableObject
from src.drawing_objects.canvas_model import CanvasModel
from src.drawing_objects.circle import Circle
from src.drawing_objects.line import Line
from src.drawing_objects.rectangle import Rectangle
from src.drawing_objects.renderer import blend_canvas, render_objects
from src.drawing_objects.stroke import Stroke
from src.drawing_objects.text import Text

__all__ = [
    "Arrow",
    "Circle",
    "CanvasModel",
    "DrawableObject",
    "Line",
    "Rectangle",
    "Stroke",
    "Text",
    "blend_canvas",
    "render_objects",
]
