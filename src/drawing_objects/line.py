"""Line shape object."""

from dataclasses import dataclass, field

import cv2
import numpy as np

from src.drawing_objects.base import DrawableObject


@dataclass
class Line(DrawableObject):
    start_point: tuple[int, int] = (0, 0)
    end_point: tuple[int, int] = (0, 0)
    type: str = field(default="line", init=False)

    def render(self, canvas: np.ndarray) -> None:
        if self.visible:
            cv2.line(canvas, self.start_point, self.end_point, self.color, self.thickness)

    def bounding_box(self) -> tuple[int, int, int, int]:
        pad = self.thickness + 4
        xs = [self.start_point[0], self.end_point[0]]
        ys = [self.start_point[1], self.end_point[1]]
        return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
