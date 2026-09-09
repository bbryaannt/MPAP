"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Classifier Tests
===============================================================================
"""

from pipeline.classifier import (
    MeltPoolClassification,
    MeltPoolClassifier,
)

from pipeline.melt_pool_features import MeltPoolFeatures

from models.band_counts import BandCounts


classifier = MeltPoolClassifier()


def make_features(
    area_px=1000,
    area_mm2=5.0,
    circularity=0.75,
):
    return MeltPoolFeatures(
        area_px=area_px,
        area_mm2=area_mm2,
        centroid_x=640.0,
        centroid_y=190.0,
        bbox_width=100,
        bbox_height=100,
        aspect_ratio=1.0,
        circularity=circularity,
    )


def make_bands(
    band3=6000,
    band4=200,
    band5=0,
):
    return BandCounts(
        band1=0,
        band2=0,
        band3=band3,
        band4=band4,
        band5=band5,
    )


def test_laser_off():
    features = make_features(area_px=0)

    bands = make_bands(
        band3=0,
        band4=0,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.LASER_OFF


def test_high_power():
    features = make_features()

    bands = make_bands(
        band3=7000,
        band4=500,
        band5=401,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.HIGH_POWER


def test_low_power_very_low_band3():
    features = make_features()

    bands = make_bands(
        band3=999,
        band4=50,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.LOW_POWER


def test_low_power_band3_below_good_threshold():
    features = make_features()

    bands = make_bands(
        band3=5000,
        band4=500,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.LOW_POWER


def test_low_power_high_band3_but_band4_below_good_threshold():
    """
    Frames with strong B3 but insufficient B4 are LOW_POWER.

    This specifically covers the transition region that previously
    produced UNKNOWN classifications.
    """

    features = make_features(
        circularity=0.69,
    )

    bands = make_bands(
        band3=6500,
        band4=175,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.LOW_POWER


def test_low_power_high_band3_band4_at_100():
    """
    B4 values at the lower transition threshold are LOW_POWER.
    """

    features = make_features(
        circularity=0.70,
    )

    bands = make_bands(
        band3=8000,
        band4=100,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.LOW_POWER


def test_low_powder():
    features = make_features(
        circularity=0.50,
    )

    bands = make_bands(
        band3=7000,
        band4=250,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.LOW_POWDER


def test_good():
    features = make_features(
        circularity=0.75,
    )

    bands = make_bands(
        band3=7000,
        band4=250,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.GOOD


def test_good_at_minimum_circularity():
    features = make_features(
        circularity=0.62,
    )

    bands = make_bands(
        band3=6000,
        band4=200,
        band5=0,
    )

    result = classifier.classify(features, bands)

    assert result == MeltPoolClassification.GOOD
