"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Classifier Test
===============================================================================
"""

from pipeline.classifier import (
    MeltPoolClassification,
    MeltPoolClassifier,
)
from pipeline.melt_pool_features import MeltPoolFeatures


def main():

    classifier = MeltPoolClassifier()

    test_cases = [
        (
            "Laser Off",
            MeltPoolFeatures(
                area_px=0,
                area_mm2=0.0,
                centroid_x=0.0,
                centroid_y=0.0,
                bbox_width=0,
                bbox_height=0,
                aspect_ratio=0.0,
                circularity=0.0,
            ),
            MeltPoolClassification.LASER_OFF,
        ),
        (
            "Low Powder",
            MeltPoolFeatures(
                area_px=1000,
                area_mm2=0.25,
                centroid_x=640.0,
                centroid_y=190.0,
                bbox_width=40,
                bbox_height=40,
                aspect_ratio=1.0,
                circularity=0.8,
            ),
            MeltPoolClassification.LOW_POWDER,
        ),
        (
            "Low Power",
            MeltPoolFeatures(
                area_px=20000,
                area_mm2=12.0,
                centroid_x=640.0,
                centroid_y=190.0,
                bbox_width=120,
                bbox_height=100,
                aspect_ratio=1.2,
                circularity=0.8,
            ),
            MeltPoolClassification.LOW_POWER,
        ),
        (
            "Low Powder - Circularity",
            MeltPoolFeatures(
                area_px=7000,
                area_mm2=4.0,
                centroid_x=640.0,
                centroid_y=190.0,
                bbox_width=100,
                bbox_height=100,
                aspect_ratio=1.0,
                circularity=0.20,
            ),
            MeltPoolClassification.LOW_POWDER,
        ),
        (
            "Good",
            MeltPoolFeatures(
                area_px=7000,
                area_mm2=4.0,
                centroid_x=640.0,
                centroid_y=190.0,
                bbox_width=100,
                bbox_height=90,
                aspect_ratio=1.11,
                circularity=0.80,
            ),
            MeltPoolClassification.GOOD,
        ),
    ]

    print("=" * 40)
    print("Melt Pool Classifier Test")
    print("=" * 40)
    print()

    passed = 0

    for name, features, expected in test_cases:

        result = classifier.classify(features)

        if result == expected:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"

        print(
            f"{status}: {name}"
            f" -> {result.value}"
            f" (expected {expected.value})"
        )

    print()
    print(f"Passed: {passed}/{len(test_cases)}")

    if passed != len(test_cases):
        raise AssertionError(
            "One or more classifier tests failed."
        )


if __name__ == "__main__":
    main()