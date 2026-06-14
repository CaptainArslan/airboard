"""Drawable object base class."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np


@dataclass
class DrawableObject(ABC):
    color: tuple[int, int, int]
    thickness: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    visible: bool = True

    @abstractmethod
    def render(self, canvas: np.ndarray) -> None:
        """Draw this object onto a BGR canvas."""

    @abstractmethod
    def bounding_box(self) -> tuple[int, int, int, int]:
        """Return (x_min, y_min, x_max, y_max)."""

    def hit_test(self, x: int, y: int, radius: int) -> bool:
        """True if eraser circle at (x,y) overlaps this object."""
        x_min, y_min, x_max, y_max = self.bounding_box()
        cx = max(x_min, min(x, x_max))
        cy = max(y_min, min(y, y_max))
        return (cx - x) ** 2 + (cy - y) ** 2 <= radius ** 2
