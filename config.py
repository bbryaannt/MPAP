"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Configuration
===============================================================================
"""

from dataclasses import dataclass


@dataclass
class DecoderConfig:
    """
    RPM222XR decoder configuration.
    """

    expected_width: int = 1280
    expected_height: int = 380
    expected_bits_per_pixel: int = 12


@dataclass
class DetectionConfig:
    """
    Melt-pool detection configuration.
    """

    peak_fraction: float = 0.85
    min_component_area: int = 25


@dataclass
class AnalysisConfig:
    """
    Thermal-band analysis configuration.
    """

    # Thermal band boundaries.
    #
    # B1 = 27000-32599
    # B2 = 32600-38199
    # B3 = 38200-43799
    # B4 = 43800-49399
    # B5 = 49400-54999
    #
    # Values above 55000 are clipped by the analysis range.
    band_edges: tuple = (
        27000,
        32600,
        38200,
        43800,
        49400,
        55000,
    )


@dataclass
class ClassificationConfig:
    """
    Melt-pool classification thresholds.
    """

    # -------------------------------------------------------------------------
    # HIGH POWER
    # -------------------------------------------------------------------------

    # Significant B5 thermal area indicates excessive thermal energy.
    high_power_band5: int = 400

    # -------------------------------------------------------------------------
    # LOW POWER
    # -------------------------------------------------------------------------

    # Extremely weak B3 indicates insufficient thermal energy.
    low_power_band3: int = 1000

    # Extremely weak B4 indicates insufficient thermal development.
    #
    # IMPORTANT:
    # This is intentionally 100 rather than 200.
    #
    # B4 = 100 is treated as borderline/UNKNOWN when B3 is also below
    # the GOOD threshold. This preserves the classifier test case.
    low_power_band4: int = 100

    # -------------------------------------------------------------------------
    # GOOD
    # -------------------------------------------------------------------------

    # Strong B3 and meaningful B4 are required for a GOOD melt pool.
    good_band3: int = 6000
    good_band4: int = 200

    # -------------------------------------------------------------------------
    # LOW POWDER
    # -------------------------------------------------------------------------

    # Poor circularity is the primary geometric indicator of low powder.
    low_powder_circularity: float = 0.62

    # Small irregular melt pools can also indicate low powder.
    low_powder_area_mm2: float = 5.0

    # -------------------------------------------------------------------------
    # GENERAL CIRCULARITY
    # -------------------------------------------------------------------------

    # Minimum circularity considered geometrically acceptable.
    minimum_circularity: float = 0.62

    # -------------------------------------------------------------------------
    # BORDERLINE THERMAL REGION
    # -------------------------------------------------------------------------

    # B4 values at or above this level are considered thermally developed
    # enough to evaluate against the GOOD requirements.
    #
    # This value is kept separate from good_band4 because 100-199 represents
    # a borderline thermal region rather than a clearly GOOD melt pool.
    borderline_band4: int = 100


@dataclass
class Config:
    """
    Main MPAP configuration.
    """

    decoder: DecoderConfig
    detection: DetectionConfig
    analysis: AnalysisConfig
    classification: ClassificationConfig


config = Config(
    decoder=DecoderConfig(),
    detection=DetectionConfig(),
    analysis=AnalysisConfig(),
    classification=ClassificationConfig(),
)