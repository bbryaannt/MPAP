"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Classifier
===============================================================================
"""

from enum import Enum

from pipeline.melt_pool_features import MeltPoolFeatures


class MeltPoolClassification(str, Enum):
    LASER_OFF = "LASER_OFF"
    LOW_POWDER = "LOW_POWDER"
    LOW_POWER = "LOW_POWER"
    GOOD = "GOOD"


class MeltPoolClassifier:
    """
    Classifies melt-pool measurements using the current MPAP rules.
    """

    def __init__(
        self,
        min_area_mm2: float = 0.5,
        max_area_mm2: float = 10.0,
        min_circularity: float = 0.40,
        min_aspect_ratio: float = 0.50,
        max_aspect_ratio: float = 2.00,
    ):
        self.min_area_mm2 = min_area_mm2
        self.max_area_mm2 = max_area_mm2
        self.min_circularity = min_circularity
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio

    def classify(
        self,
        features: MeltPoolFeatures,
    ) -> MeltPoolClassification:

        if features.area_px == 0:
            return MeltPoolClassification.LASER_OFF

        if features.area_mm2 < self.min_area_mm2:
            return MeltPoolClassification.LOW_POWDER

        if features.area_mm2 > self.max_area_mm2:
            return MeltPoolClassification.LOW_POWER

        if (
            features.circularity < self.min_circularity
            or features.aspect_ratio < self.min_aspect_ratio
            or features.aspect_ratio > self.max_aspect_ratio
        ):
            return MeltPoolClassification.LOW_POWDER

        return MeltPoolClassification.GOOD