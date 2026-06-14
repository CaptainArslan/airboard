"""Freehand stroke object."""

from dataclasses import dataclass, field

import cv2
import numpy as np

from src.drawing_objects.base import DrawableObject


@dataclass
class Stroke(DrawableObject):
    points: list[tuple[int, int]] = field(default_factory=list)
    type: str = field(default="stroke", init=False)

    def render(self, canvas: np.ndarray) -> None:
        if not self.visible or len(self.points) < 2:
            if self.visible and len(self.points) == 1:
                p = self.map_point(*self.points[0])
                cv2.circle(canvas, p, max(1, self.thickness // 2), self.color, -1)
            return
        mapped = [self.map_point(x, y) for x, y in self.points]
        for i in range(1, len(mapped)):
            cv2.line(canvas, mapped[i - 1], mapped[i], self.color, self.thickness)

    def _local_bounding_box(self) -> tuple[int, int, int, int]:
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        pad = self.thickness + 2
        return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
