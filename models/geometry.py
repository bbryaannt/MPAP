"""
===============================================================================
MPAP

Geometry Model

Stores geometric properties of a detected melt pool.
===============================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Geometry:
    """
    Geometric properties of a melt pool.
    """

    area_px: float
    area_mm2: float

    circularity: float
    aspect_ratio: float

    @property
    def is_circular(self) -> bool:
        """
        Returns True if the melt pool is approximately circular.
        """
        return self.circularity >= 0.75