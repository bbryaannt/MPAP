"""
===============================================================================
MPAP

Thermal Model

Stores thermal measurements extracted from one frame.
===============================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Thermal:
    """
    Thermal properties of a melt pool.
    """

    mean_intensity: float
    max_intensity: float
    threshold: float

    @property
    def temperature_range(self) -> float:
        """
        Difference between the hottest pixel and the threshold.
        """
        return self.max_intensity - self.threshold