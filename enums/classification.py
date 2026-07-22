"""
===============================================================================
MPAP

Classification Enumeration
===============================================================================
"""

from enum import Enum


class Classification(Enum):
    """
    Possible melt pool classifications.
    """

    GOOD = "GOOD"

    HIGH_POWER = "HIGH_POWER"

    LOW_POWER = "LOW_POWER"

    LOW_POWDER = "LOW_POWDER"

    LASER_OFF = "LASER_OFF"

    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value