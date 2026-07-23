"""
===============================================================================
MPAP

Statistics Model

Stores descriptive statistics for a single metric.
===============================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Statistics:
    """
    Descriptive statistics for a single metric.
    """

    mean: float
    median: float
    standard_deviation: float

    minimum: float
    maximum: float

    @property
    def range(self) -> float:
        """Maximum minus minimum."""
        return self.maximum - self.minimum

    @property
    def variation(self) -> float:
        """
        Coefficient of variation (%).

        Returns 0 if the mean is zero.
        """
        if self.mean == 0:
            return 0.0

        return (
            self.standard_deviation
            / self.mean
        ) * 100