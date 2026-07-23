"""
===============================================================================
MPAP

Layer Statistics Model

Stores statistical summaries for one physical layer.
===============================================================================
"""

from dataclasses import dataclass

from models import Statistics


@dataclass(frozen=True, slots=True)
class LayerStatistics:
    """
    Statistical summary of one layer.
    """

    # Geometry
    area_px: Statistics
    area_mm2: Statistics
    circularity: Statistics
    aspect_ratio: Statistics

    # Thermal
    mean_intensity: Statistics
    max_intensity: Statistics
    threshold: Statistics

    # Classification percentages
    good_percentage: float
    low_power_percentage: float
    low_powder_percentage: float
    high_power_percentage: float
    laser_off_percentage: float

    # General
    frame_count: int
    measured_frame_count: int

    @property
    def measurement_percentage(self) -> float:

        if self.frame_count == 0:
            return 0.0

        return (
            self.measured_frame_count
            / self.frame_count
        ) * 100