"""Drawable object base class with transform support."""

from __future__ import annotations

import copy
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from src.drawing_objects.transform import bbox_from_points, transform_point


@dataclass
class DrawableObject(ABC):
    color: tuple[int, int, int]
    thickness: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    visible: bool = True
    offset_x: float = 0.0
    offset_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    z_index: int = 0
    selected: bool = False
    group_id: str | None = None

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def pivot(self) -> tuple[float, float]:
        x0, y0, x1, y1 = self._local_bounding_box()
        return (x0 + x1) / 2, (y0 + y1) / 2

    def map_point(self, x: float, y: float) -> tuple[int, int]:
        px, py = self.pivot()
        return transform_point(
            x, y, px, py,
            self.scale_x, self.scale_y, self.rotation,
            self.offset_x, self.offset_y,
        )

    def move_by(self, dx: float, dy: float) -> None:
        self.offset_x += dx
        self.offset_y += dy
        self.touch()

    def set_scale(self, sx: float, sy: float | None = None) -> None:
        self.scale_x = max(0.05, sx)
        self.scale_y = max(0.05, sy if sy is not None else sx)
        self.touch()

    def add_rotation(self, degrees: float) -> None:
        self.rotation = (self.rotation + degrees) % 360
        self.touch()

    @abstractmethod
    def _local_bounding_box(self) -> tuple[int, int, int, int]:
        """Axis-aligned bounds in local space (before transform)."""

    def bounding_box(self) -> tuple[int, int, int, int]:
        x0, y0, x1, y1 = self._local_bounding_box()
        corners = [
            self.map_point(x0, y0),
            self.map_point(x1, y0),
            self.map_point(x0, y1),
            self.map_point(x1, y1),
        ]
        return bbox_from_points(corners)

    def center(self) -> tuple[int, int]:
        x0, y0, x1, y1 = self.bounding_box()
        return (x0 + x1) // 2, (y0 + y1) // 2

    def hit_test(self, x: int, y: int, radius: int = 0) -> bool:
        x_min, y_min, x_max, y_max = self.bounding_box()
        pad = radius + 4
        cx = max(x_min - pad, min(x, x_max + pad))
        cy = max(y_min - pad, min(y, y_max + pad))
        return (cx - x) ** 2 + (cy - y) ** 2 <= (pad + 8) ** 2

    def distance_to_point(self, x: int, y: int) -> float:
        cx, cy = self.center()
        return ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5

    @abstractmethod
    def render(self, canvas: np.ndarray) -> None:
        """Draw this object onto a BGR canvas."""

    def duplicate(self, dx: int = 20, dy: int = 20) -> DrawableObject:
        clone = copy.deepcopy(self)
        clone.id = str(uuid.uuid4())
        clone.selected = False
        clone.offset_x += dx
        clone.offset_y += dy
        clone.created_at = datetime.now(timezone.utc).isoformat()
        clone.updated_at = clone.created_at
        return clone
