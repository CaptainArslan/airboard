"""Arrow shape object."""

from dataclasses import dataclass, field

import cv2
import numpy as np

from src.drawing_objects.base import DrawableObject


@dataclass
class Arrow(DrawableObject):
    start_point: tuple[int, int] = (0, 0)
    end_point: tuple[int, int] = (0, 0)
    type: str = field(default="arrow", init=False)

    def render(self, canvas: np.ndarray) -> None:
        if self.visible:
            a = self.map_point(*self.start_point)
            b = self.map_point(*self.end_point)
            cv2.arrowedLine(
                canvas, a, b, self.color, self.thickness, tipLength=0.25,
            )

    def _local_bounding_box(self) -> tuple[int, int, int, int]:
        pad = self.thickness + 8
        xs = [self.start_point[0], self.end_point[0]]
        ys = [self.start_point[1], self.end_point[1]]
        return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
