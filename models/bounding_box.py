"""
===============================================================================
MPAP

Bounding Box Model
===============================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:

    x: int
    y: int

    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2