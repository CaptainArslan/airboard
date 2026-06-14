"""Object-based canvas with undo/redo."""

from __future__ import annotations

import copy
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from src.drawing_objects.base import DrawableObject
from src.drawing_objects.eraser_engine import apply_eraser_to_objects
from src.drawing_objects.renderer import blend_canvas, render_objects


class CanvasModel:
    """Stores drawable objects and history snapshots."""

    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self._objects: list[DrawableObject] = []
        self._history: list[list[DrawableObject]] = [[]]
        self._history_index = 0
        self._erase_batch_active = False
        self._erase_batch_modified = False
        self._manip_batch_active = False
        self._manip_batch_modified = False
        self._next_z = 0

    @property
    def objects(self) -> list[DrawableObject]:
        return self._objects

    def resize(self, width: int, height: int) -> None:
        if width == self.width and height == self.height:
            return
        if self.width > 0 and self.height > 0 and self._objects:
            sx = width / self.width
            sy = height / self.height
            self._scale_objects(sx, sy)
        self.width = width
        self.height = height

    def _scale_point(self, p: tuple[int, int], sx: float, sy: float) -> tuple[int, int]:
        return int(p[0] * sx), int(p[1] * sy)

    def _scale_objects(self, sx: float, sy: float) -> None:
        from src.drawing_objects.arrow import Arrow
        from src.drawing_objects.circle import Circle
        from src.drawing_objects.line import Line
        from src.drawing_objects.rectangle import Rectangle
        from src.drawing_objects.stroke import Stroke
        from src.drawing_objects.text import Text

        scaled: list[DrawableObject] = []
        for obj in self._objects:
            if isinstance(obj, Stroke):
                obj.points = [self._scale_point(p, sx, sy) for p in obj.points]
            elif isinstance(obj, Line):
                obj.start_point = self._scale_point(obj.start_point, sx, sy)
                obj.end_point = self._scale_point(obj.end_point, sx, sy)
            elif isinstance(obj, Rectangle):
                obj.start_point = self._scale_point(obj.start_point, sx, sy)
                obj.end_point = self._scale_point(obj.end_point, sx, sy)
            elif isinstance(obj, Circle):
                obj.center_point = self._scale_point(obj.center_point, sx, sy)
                obj.radius = max(1, int(obj.radius * (sx + sy) / 2))
            elif isinstance(obj, Arrow):
                obj.start_point = self._scale_point(obj.start_point, sx, sy)
                obj.end_point = self._scale_point(obj.end_point, sx, sy)
            elif isinstance(obj, Text):
                obj.position = self._scale_point(obj.position, sx, sy)
                obj.font_size = max(12, int(obj.font_size * (sx + sy) / 2))
            scaled.append(obj)
        self._objects = scaled
        self._history = [copy.deepcopy(self._objects)]
        self._history_index = 0

    def _snapshot(self) -> list[DrawableObject]:
        return copy.deepcopy(self._objects)

    def _push_history(self) -> None:
        self._history = self._history[: self._history_index + 1]
        self._history.append(self._snapshot())
        self._history_index += 1

    def add_object(self, obj: DrawableObject) -> None:
        obj.z_index = self._next_z
        self._next_z += 1
        self._objects.append(obj)
        self._push_history()

    def begin_manipulation_batch(self) -> None:
        self._manip_batch_active = True
        self._manip_batch_modified = False

    def end_manipulation_batch(self) -> None:
        if self._manip_batch_active and self._manip_batch_modified:
            self._push_history()
        self._manip_batch_active = False
        self._manip_batch_modified = False

    def commit_manipulation(self) -> None:
        self._push_history()

    def mark_manipulation_changed(self) -> None:
        self._mark_manipulated()

    def _mark_manipulated(self) -> None:
        if self._manip_batch_active:
            self._manip_batch_modified = True
        else:
            self._push_history()

    def delete_objects(self, ids: set[str]) -> None:
        before = len(self._objects)
        self._objects = [o for o in self._objects if o.id not in ids]
        if len(self._objects) != before:
            self._push_history()

    def duplicate_objects(self, ids: set[str]) -> list[DrawableObject]:
        clones = []
        for obj in self._objects:
            if obj.id in ids:
                clone = obj.duplicate()
                clone.z_index = self._next_z
                self._next_z += 1
                clones.append(clone)
        if clones:
            self._objects.extend(clones)
            self._push_history()
        return clones

    def layer_selected(self, ids: set[str], delta: int) -> None:
        if not ids:
            return
        for obj in self._objects:
            if obj.id in ids:
                obj.z_index += delta
                obj.touch()
        self._objects.sort(key=lambda o: o.z_index)
        self._push_history()

    def remove_object(self, obj_id: str) -> bool:
        for i, obj in enumerate(self._objects):
            if obj.id == obj_id:
                self._objects.pop(i)
                self._push_history()
                return True
        return False

    def remove_objects_at(self, x: int, y: int, radius: int) -> int:
        """Legacy whole-object erase; prefer apply_eraser."""
        return 1 if self.apply_eraser(x, y, radius) else 0

    def begin_erase_batch(self) -> None:
        """Start batched erase session (one undo step on commit)."""
        self._erase_batch_active = True
        self._erase_batch_modified = False

    def end_erase_batch(self) -> None:
        """Commit batched erase to undo history."""
        if self._erase_batch_active and self._erase_batch_modified:
            self._push_history()
        self._erase_batch_active = False
        self._erase_batch_modified = False

    def apply_eraser(self, x: int, y: int, radius: int) -> bool:
        """Erase at position with partial stroke support. Returns True if changed."""
        new_objects, changed = apply_eraser_to_objects(self._objects, x, y, radius)
        if not changed:
            return False
        self._objects = new_objects
        if self._erase_batch_active:
            self._erase_batch_modified = True
        else:
            self._push_history()
        return True

    def export_composite(self, path: str | Path, background: np.ndarray) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        layer = self.render(self.width, self.height)
        out = blend_canvas(background, layer)
        cv2.imwrite(str(path), out)
        return path

    @staticmethod
    def make_export_path(base_dir: str | Path) -> Path:
        base_dir = Path(base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("airboard_%Y%m%d_%H%M%S.png")
        return base_dir / stamp

    def undo(self) -> bool:
        if self._history_index <= 0:
            return False
        self._history_index -= 1
        self._objects = copy.deepcopy(self._history[self._history_index])
        return True

    def redo(self) -> bool:
        if self._history_index >= len(self._history) - 1:
            return False
        self._history_index += 1
        self._objects = copy.deepcopy(self._history[self._history_index])
        return True

    def clear(self) -> None:
        if not self._objects:
            return
        self._objects.clear()
        self._push_history()

    def render(self, width: int | None = None, height: int | None = None) -> np.ndarray:
        w = width or self.width
        h = height or self.height
        return render_objects(self._objects, w, h)

    def export_png(self, path: str | Path, background: np.ndarray | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        layer = self.render()
        if background is not None:
            out = blend_canvas(background, layer)
        else:
            out = layer
        cv2.imwrite(str(path), out)
        return path
