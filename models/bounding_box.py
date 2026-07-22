"""
===============================================================================
MPAP

Bounding Box Model

Represents an axis-aligned bounding box in image coordinates.
===============================================================================
"""

from dataclasses import dataclass

from .point import Point


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """
    Represents a rectangular region in image coordinates.
    """

    x: int
    y: int

    width: int
    height: int

    @property
    def area(self) -> int:
        """Bounding box area in pixels."""
        return self.width * self.height

    @property
    def center(self) -> Point:
        """Return the center of the bounding box."""
        return Point(
            self.x + self.width / 2,
            self.y + self.height / 2,
        )

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.height