import math

import cv2
import numpy as np

from src.config import settings
from src.drawing import tools


class Canvas:
    """Permanent drawing layer with per-hand freehand and shape support."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self._previous_points: dict[str, tuple[int, int] | None] = {
            label: None for label in settings.HAND_LABELS
        }
        self._previous_erase_points: dict[str, tuple[int, int] | None] = {}
        self._color_index = settings.DEFAULT_COLOR_INDEX
        self.color = settings.COLORS[self._color_index]

    def resize(self, width, height):
        if width == self.width and height == self.height:
            return
        if self.width > 0 and self.height > 0 and np.any(self._canvas):
            self._canvas = cv2.resize(self._canvas, (width, height), interpolation=cv2.INTER_LINEAR)
        else:
            self._canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.width = width
        self.height = height
        self.reset_all_previous_points()
        self._previous_erase_points.clear()

    def set_color(self, color):
        self.color = color

    def set_color_by_index(self, index):
        if 0 <= index < len(settings.COLORS):
            self._color_index = index
            self.color = settings.COLORS[index]

    @property
    def color_index(self):
        return self._color_index

    def reset_previous_point(self, hand_label: str):
        if hand_label in self._previous_points:
            self._previous_points[hand_label] = None

    def reset_all_previous_points(self):
        for label in self._previous_points:
            self._previous_points[label] = None

    def reset_previous_erase_point(self, hand_label: str | None = None):
        if hand_label is None:
            self._previous_erase_points.clear()
        else:
            self._previous_erase_points.pop(hand_label, None)

    def draw_to(self, point, hand_label: str, color=None, thickness=None):
        """Draw freehand segment for one hand only."""
        if point is None:
            self.reset_previous_point(hand_label)
            return

        color = color or self.color
        thickness = thickness or settings.BRUSH_THICKNESS
        prev = self._previous_points.get(hand_label)

        if prev is not None:
            dist_sq = (point[0] - prev[0]) ** 2 + (point[1] - prev[1]) ** 2
            if dist_sq >= settings.MIN_DRAW_DISTANCE ** 2:
                cv2.line(self._canvas, prev, point, color, thickness)
                self._previous_points[hand_label] = point
        else:
            self._previous_points[hand_label] = point

    def draw_line_shape(self, start, end, color, thickness):
        cv2.line(self._canvas, start, end, color, thickness)

    def draw_rectangle(self, start, end, color, thickness):
        cv2.rectangle(self._canvas, start, end, color, thickness)

    def draw_circle(self, start, end, color, thickness):
        radius = max(int(math.hypot(end[0] - start[0], end[1] - start[1])), 1)
        cv2.circle(self._canvas, start, radius, color, thickness)

    def draw_arrow(self, start, end, color, thickness):
        cv2.arrowedLine(
            self._canvas, start, end, color, thickness, tipLength=0.25,
        )

    def commit_shape(self, tool, start, end, color, thickness):
        if start is None or end is None:
            return
        if tool == tools.LINE:
            self.draw_line_shape(start, end, color, thickness)
        elif tool == tools.RECTANGLE:
            self.draw_rectangle(start, end, color, thickness)
        elif tool == tools.CIRCLE:
            self.draw_circle(start, end, color, thickness)
        elif tool == tools.ARROW:
            self.draw_arrow(start, end, color, thickness)

    @staticmethod
    def draw_shape_preview(frame, tool, start, end, color, thickness):
        """Draw non-permanent shape preview onto display frame."""
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
            cv2.arrowedLine(
                frame, start, end, preview_color, thickness, tipLength=0.25,
            )

    def erase_at(self, x, y, radius=None):
        if radius is None:
            radius = settings.ERASER_RADIUS
        cv2.circle(self._canvas, (int(x), int(y)), radius, (0, 0, 0), -1)

    def erase_to(self, point, hand_label: str, radius=None):
        if point is None:
            self.reset_previous_erase_point(hand_label)
            return
        if radius is None:
            radius = settings.ERASER_RADIUS

        prev = self._previous_erase_points.get(hand_label)
        if prev is not None:
            dist_sq = (point[0] - prev[0]) ** 2 + (point[1] - prev[1]) ** 2
            if dist_sq >= settings.MIN_DRAW_DISTANCE ** 2:
                cv2.line(self._canvas, prev, point, (0, 0, 0), radius * 2)
                self._previous_erase_points[hand_label] = point
        else:
            self.erase_at(point[0], point[1], radius)
            self._previous_erase_points[hand_label] = point

    def clear(self):
        self._canvas[:] = 0
        self.reset_all_previous_points()
        self._previous_erase_points.clear()

    def blend(self, frame):
        mask = cv2.cvtColor(self._canvas, cv2.COLOR_BGR2GRAY)
        has_drawing = mask > 0
        if not np.any(has_drawing):
            return frame

        blended = frame.copy()
        overlay = cv2.addWeighted(
            frame, 1 - settings.CANVAS_ALPHA,
            self._canvas, settings.CANVAS_ALPHA,
            0,
        )
        blended[has_drawing] = overlay[has_drawing]
        return blended
