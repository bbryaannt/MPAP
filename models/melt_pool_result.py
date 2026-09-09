"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Result Model
===============================================================================
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class MeltPoolResult:
    """
    Complete analysis result for one melt-pool frame.
    """

    frame_number: int
    features: Any
    band_counts: Any
    classification: Any