"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Classifier
===============================================================================
"""

from enum import Enum

from config import config as mpap_config

from models.band_counts import BandCounts

from pipeline.melt_pool_features import MeltPoolFeatures


class MeltPoolClassification(Enum):
    LASER_OFF = "LASER_OFF"
    LOW_POWER = "LOW_POWER"
    LOW_POWDER = "LOW_POWDER"
    GOOD = "GOOD"
    HIGH_POWER = "HIGH_POWER"
    UNKNOWN = "UNKNOWN"


class MeltPoolClassifier:
    """
    Rule-based melt pool classifier.
    """

    def __init__(self, config=None):
        self.config = (
            config
            if config is not None
            else mpap_config.classification
        )

    def classify(
        self,
        features: MeltPoolFeatures,
        bands: BandCounts,
    ) -> MeltPoolClassification:

        # ---------------------------------------------------------------
        # Laser off
        # ---------------------------------------------------------------

        if features.area_px <= 0:
            return MeltPoolClassification.LASER_OFF

        # ---------------------------------------------------------------
        # High power
        # ---------------------------------------------------------------

        if bands.band5 > self.config.high_power_band5:
            return MeltPoolClassification.HIGH_POWER

        # ---------------------------------------------------------------
        # Very low power
        # ---------------------------------------------------------------

        if bands.band3 < self.config.low_power_band3:
            return MeltPoolClassification.LOW_POWER

        # ---------------------------------------------------------------
        # Low power
        #
        # B3 below the GOOD threshold indicates insufficient thermal
        # energy even if some hotter B4 pixels are present.
        # ---------------------------------------------------------------

        if bands.band3 < self.config.good_band3:
            return MeltPoolClassification.LOW_POWER

        # ---------------------------------------------------------------
        # Low power
        #
        # B3 has reached the GOOD range, but B4 has not reached the
        # required GOOD threshold.
        #
        # This captures the transitional region:
        #
        #     B3 >= good_band3
        #     B4 < good_band4
        #
        # These frames previously fell through to UNKNOWN.
        # ---------------------------------------------------------------

        if bands.band4 < self.config.good_band4:
            return MeltPoolClassification.LOW_POWER

        # ---------------------------------------------------------------
        # Low powder
        #
        # Adequate thermal intensity is present, but the melt pool
        # geometry is insufficiently circular.
        # ---------------------------------------------------------------

        if features.circularity < self.config.low_powder_circularity:
            return MeltPoolClassification.LOW_POWDER

        # ---------------------------------------------------------------
        # Good
        #
        # B3 and B4 are both sufficiently developed and the melt pool
        # geometry is sufficiently circular.
        # ---------------------------------------------------------------

        if (
            bands.band3 >= self.config.good_band3
            and bands.band4 >= self.config.good_band4
            and features.circularity >= self.config.minimum_circularity
        ):
            return MeltPoolClassification.GOOD

        # ---------------------------------------------------------------
        # Fallback
        # ---------------------------------------------------------------

        return MeltPoolClassification.UNKNOWN
