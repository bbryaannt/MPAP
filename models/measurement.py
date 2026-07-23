"""
===============================================================================
MPAP

Measurement Model

Represents every measurable property of a single detected melt pool.
===============================================================================
"""

from dataclasses import dataclass

from models import (
    BandCounts,
    BoundingBox,
    Geometry,
    Point,
    Thermal,
)

from enums import Classification


@dataclass(slots=True)
class Measurement:
    """
    Complete description of one detected melt pool.
    """

    geometry: Geometry

    thermal: Thermal

    band_counts: BandCounts

    geometry_center: Point

    intensity_center: Point

    bounding_box: BoundingBox

    classification: Classification

    classification_reason: str | None = None

    @property
    def is_good(self) -> bool:
        return self.classification == Classification.GOOD

    def to_dict(self) -> dict:
        """
        Export measurement as a dictionary.
        """

        return {

            "Area_px": self.geometry.area_px,
            "Area_mm2": self.geometry.area_mm2,

            "Circularity": self.geometry.circularity,
            "Aspect_Ratio": self.geometry.aspect_ratio,

            "Mean_Intensity": self.thermal.mean_intensity,
            "Max_Intensity": self.thermal.max_intensity,
            "Threshold": self.thermal.threshold,

            "Geo_X": self.geometry_center.x,
            "Geo_Y": self.geometry_center.y,

            "Weighted_X": self.intensity_center.x,
            "Weighted_Y": self.intensity_center.y,

            "BBox_X": self.bounding_box.x,
            "BBox_Y": self.bounding_box.y,
            "BBox_Width": self.bounding_box.width,
            "BBox_Height": self.bounding_box.height,

            "Band1_Count": self.band_counts.band1,
            "Band2_Count": self.band_counts.band2,
            "Band3_Count": self.band_counts.band3,
            "Band4_Count": self.band_counts.band4,
            "Band5_Count": self.band_counts.band5,

            "Classification": str(self.classification),
            "Classification_Reason": self.classification_reason,
        }