"""Circle shape object."""

import math
from dataclasses import dataclass, field

import cv2
import numpy as np

from src.drawing_objects.base import DrawableObject


@dataclass
class Circle(DrawableObject):
    center_point: tuple[int, int] = (0, 0)
    radius: int = 1
    type: str = field(default="circle", init=False)

    @classmethod
    def from_points(
        cls,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        thickness: int,
    ) -> "Circle":
        radius = max(int(math.hypot(end[0] - start[0], end[1] - start[1])), 1)
        return cls(center_point=start, radius=radius, color=color, thickness=thickness)

    def render(self, canvas: np.ndarray) -> None:
        if self.visible:
            center = self.map_point(*self.center_point)
            r = max(1, int(self.radius * (self.scale_x + self.scale_y) / 2))
            cv2.circle(canvas, center, r, self.color, self.thickness)

    def _local_bounding_box(self) -> tuple[int, int, int, int]:
        pad = self.thickness + 4
        cx, cy = self.center_point
        r = self.radius + pad
        return (cx - r, cy - r, cx + r, cy + r)
