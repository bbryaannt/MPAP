"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Feature Extraction
===============================================================================
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class MeltPoolFeatures:
    """
    Measured geometric features of a detected melt pool.
    """

    area_px: float
    area_mm2: float

    centroid_x: float
    centroid_y: float

    bbox_width: int
    bbox_height: int

    aspect_ratio: float
    circularity: float


class MeltPoolFeatureExtractor:
    """
    Extract geometric features from a binary melt-pool mask.
    """

    def __init__(
        self,
        pixels_per_mm: float = 40.0,
    ):
        if pixels_per_mm <= 0:
            raise ValueError(
                "pixels_per_mm must be greater than zero."
            )

        self.pixels_per_mm = pixels_per_mm

    def extract(
        self,
        mask: np.ndarray,
    ) -> MeltPoolFeatures:
        """
        Extract measurements from the largest connected melt-pool contour.
        """

        if mask.ndim != 2:
            raise ValueError(
                "Melt-pool mask must be a 2-D array."
            )

        mask = mask.astype(np.uint8)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )

        if not contours:
            return MeltPoolFeatures(
                area_px=0.0,
                area_mm2=0.0,
                centroid_x=0.0,
                centroid_y=0.0,
                bbox_width=0,
                bbox_height=0,
                aspect_ratio=0.0,
                circularity=0.0,
            )

        contour = max(
            contours,
            key=cv2.contourArea,
        )

        area_px = float(
            cv2.contourArea(contour)
        )

        area_mm2 = (
            area_px /
            (self.pixels_per_mm ** 2)
        )

        moments = cv2.moments(contour)

        if moments["m00"] != 0:
            centroid_x = (
                moments["m10"] /
                moments["m00"]
            )

            centroid_y = (
                moments["m01"] /
                moments["m00"]
            )
        else:
            centroid_x = 0.0
            centroid_y = 0.0

        x, y, width, height = cv2.boundingRect(
            contour
        )

        aspect_ratio = (
            width / height
            if height > 0
            else 0.0
        )

        perimeter = cv2.arcLength(
            contour,
            True,
        )

        if perimeter > 0:
            circularity = (
                4.0 *
                np.pi *
                area_px /
                (perimeter ** 2)
            )
        else:
            circularity = 0.0

        return MeltPoolFeatures(
            area_px=area_px,
            area_mm2=area_mm2,
            centroid_x=float(centroid_x),
            centroid_y=float(centroid_y),
            bbox_width=int(width),
            bbox_height=int(height),
            aspect_ratio=float(aspect_ratio),
            circularity=float(circularity),
        )