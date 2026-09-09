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

    The extractor cleans small isolated components before measuring
    the melt-pool geometry. This prevents small disconnected thermal
    regions from distorting the contour calculation.
    """

    def __init__(
        self,
        pixels_per_mm: float = 40.0,
        minimum_component_area: int = 25,
        morphology_kernel_size: int = 5,
    ):
        if pixels_per_mm <= 0:
            raise ValueError(
                "pixels_per_mm must be greater than zero."
            )

        if minimum_component_area < 1:
            raise ValueError(
                "minimum_component_area must be at least 1."
            )

        if morphology_kernel_size < 1:
            raise ValueError(
                "morphology_kernel_size must be at least 1."
            )

        if morphology_kernel_size % 2 == 0:
            raise ValueError(
                "morphology_kernel_size must be odd."
            )

        self.pixels_per_mm = pixels_per_mm
        self.minimum_component_area = minimum_component_area
        self.morphology_kernel_size = morphology_kernel_size

    def _clean_mask(
        self,
        mask: np.ndarray,
    ) -> np.ndarray:
        """
        Remove small isolated components and connect nearby regions.
        """

        binary = (
            mask.astype(np.uint8) * 255
        )

        # ---------------------------------------------------------------
        # Remove small connected components
        # ---------------------------------------------------------------

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary,
            connectivity=8,
        )

        cleaned = np.zeros_like(binary)

        for label in range(1, num_labels):

            area = stats[label, cv2.CC_STAT_AREA]

            if area >= self.minimum_component_area:
                cleaned[labels == label] = 255

        # ---------------------------------------------------------------
        # Morphological closing
        #
        # This connects nearby thermal regions that belong to the
        # same melt pool while filling small gaps in the boundary.
        # ---------------------------------------------------------------

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (
                self.morphology_kernel_size,
                self.morphology_kernel_size,
            ),
        )

        cleaned = cv2.morphologyEx(
            cleaned,
            cv2.MORPH_CLOSE,
            kernel,
        )

        return cleaned

    def extract(
        self,
        mask: np.ndarray,
    ) -> MeltPoolFeatures:
        """
        Extract measurements from the cleaned melt-pool mask.
        """

        if mask.ndim != 2:
            raise ValueError(
                "Melt-pool mask must be a 2-D array."
            )

        if mask.size == 0:
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

        # ---------------------------------------------------------------
        # Clean mask
        # ---------------------------------------------------------------

        cleaned = self._clean_mask(mask)

        # ---------------------------------------------------------------
        # Find connected melt-pool contours
        # ---------------------------------------------------------------

        contours, _ = cv2.findContours(
            cleaned,
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

        # ---------------------------------------------------------------
        # Use the largest remaining melt-pool component
        # ---------------------------------------------------------------

        contour = max(
            contours,
            key=cv2.contourArea,
        )

        area_px = float(
            cv2.contourArea(contour)
        )

        if area_px <= 0:
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

        # ---------------------------------------------------------------
        # Convert area to mm²
        # ---------------------------------------------------------------

        area_mm2 = (
            area_px /
            (self.pixels_per_mm ** 2)
        )

        # ---------------------------------------------------------------
        # Centroid
        # ---------------------------------------------------------------

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

        # ---------------------------------------------------------------
        # Bounding box
        # ---------------------------------------------------------------

        x, y, width, height = cv2.boundingRect(
            contour
        )

        aspect_ratio = (
            width / height
            if height > 0
            else 0.0
        )

        # ---------------------------------------------------------------
        # Circularity
        #
        # Circularity = 4πA / P²
        #
        # A perfectly circular contour approaches 1.
        # More irregular contours approach 0.
        # ---------------------------------------------------------------

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