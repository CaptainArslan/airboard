"""Application state enums and dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.drawing_objects.stroke import Stroke


class ToolMode(str, Enum):
    FREEHAND = "freehand"
    LINE = "line"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ARROW = "arrow"
    TEXT = "text"
    ERASER = "eraser"
    CLEAR = "clear"
    SELECT = "select"


class HandMode(str, Enum):
    IDLE = "idle"
    DRAW = "draw"
    POINTER = "pointer"
    ERASER = "eraser"
    FIST = "fist"


class GestureType(str, Enum):
    IDLE = "idle"
    DRAW = "draw"
    POINTER = "pointer"
    ERASER = "eraser"
    FIST = "fist"


@dataclass
class HandState:
    label: str
    mode: HandMode = HandMode.IDLE
    current_point: tuple[int, int] | None = None
    previous_point: tuple[int, int] | None = None
    active_stroke: Stroke | None = None
    shape_start_point: tuple[int, int] | None = None
    shape_preview_point: tuple[int, int] | None = None


@dataclass
class AppState:
    current_tool: ToolMode = ToolMode.FREEHAND
    selected_color_index: int = 0
    brush_size: int = 6
    eraser_size: int = 30
    is_fullscreen: bool = False
    show_help: bool = False
    frame_width: int = 640
    frame_height: int = 480
    text_input_active: bool = False
    text_draft: str = ""
    text_position: tuple[int, int] | None = None

    @property
    def current_frame_size(self) -> tuple[int, int]:
        return self.frame_width, self.frame_height
