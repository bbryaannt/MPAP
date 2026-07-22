"""
===============================================================================
MPAP

Point Model

Represents a 2D point in image coordinates.
===============================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    """
    Represents a point in image space.

    Parameters
    ----------
    x : float
        X coordinate in pixels.

    y : float
        Y coordinate in pixels.
    """

    x: float
    y: float

    def to_tuple(self) -> tuple[float, float]:
        """Return the point as an (x, y) tuple."""
        return (self.x, self.y)

    def distance_to(self, other: "Point") -> float:
        """Compute Euclidean distance to another point."""
        return (
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2
        ) ** 0.5