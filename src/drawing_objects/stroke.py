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
                cv2.circle(canvas, self.points[0], max(1, self.thickness // 2), self.color, -1)
            return
        for i in range(1, len(self.points)):
            cv2.line(canvas, self.points[i - 1], self.points[i], self.color, self.thickness)

    def bounding_box(self) -> tuple[int, int, int, int]:
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        pad = self.thickness + 2
        return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
