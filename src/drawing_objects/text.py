"""Text object."""

from dataclasses import dataclass, field

import cv2
import numpy as np

from src.drawing_objects.base import DrawableObject


@dataclass
class Text(DrawableObject):
    position: tuple[int, int] = (0, 0)
    content: str = ""
    font_size: int = 24
    type: str = field(default="text", init=False)

    def render(self, canvas: np.ndarray) -> None:
        if not self.visible or not self.content:
            return
        pos = self.map_point(*self.position)
        scale = max(0.4, self.font_size / 32.0) * self.scale_x
        thickness = max(1, int(self.font_size // 12))
        cv2.putText(
            canvas, self.content, pos,
            cv2.FONT_HERSHEY_SIMPLEX, scale, self.color, thickness, cv2.LINE_AA,
        )

    def _local_bounding_box(self) -> tuple[int, int, int, int]:
        if not self.content:
            return (self.position[0], self.position[1], self.position[0], self.position[1])
        scale = max(0.4, self.font_size / 32.0)
        w = int(len(self.content) * self.font_size * 0.55)
        h = int(self.font_size * 1.4)
        x, y = self.position
        return (x, y - h, x + w, y + 4)
