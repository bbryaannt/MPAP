"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Detector
===============================================================================
"""

import numpy as np

from models import DecodedImage


class MeltPoolDetector:
    """
    Detects the melt-pool region within a decoded RPM222XR image.

    The detector creates a binary mask using an intensity threshold and
    restricts the search to a region of interest around the image center.
    """

    def __init__(
        self,
        roi_half_height: int = 120,
        roi_half_width: int = 250,
    ):
        self.roi_half_height = roi_half_height
        self.roi_half_width = roi_half_width

    def create_roi_mask(
        self,
        decoded: DecodedImage,
    ) -> np.ndarray:
        """
        Create a rectangular region-of-interest mask centered on the image.
        """

        height = decoded.height
        width = decoded.width

        center_y = height // 2
        center_x = width // 2

        y_start = max(
            0,
            center_y - self.roi_half_height,
        )

        y_end = min(
            height,
            center_y + self.roi_half_height,
        )

        x_start = max(
            0,
            center_x - self.roi_half_width,
        )

        x_end = min(
            width,
            center_x + self.roi_half_width,
        )

        roi_mask = np.zeros(
            (height, width),
            dtype=bool,
        )

        roi_mask[
            y_start:y_end,
            x_start:x_end,
        ] = True

        return roi_mask

    def threshold(
        self,
        decoded: DecodedImage,
        threshold: int,
    ) -> np.ndarray:
        """
        Detect pixels at or above the specified intensity threshold.
        """

        roi_mask = self.create_roi_mask(decoded)

        intensity_mask = (
            decoded.image >= threshold
        )

        return intensity_mask & roi_mask

    def threshold_from_peak(
        self,
        decoded: DecodedImage,
        peak_fraction: float = 0.85,
    ) -> np.ndarray:
        """
        Detect the melt pool using a fraction of the image peak intensity.
        """

        if not 0 < peak_fraction <= 1:
            raise ValueError(
                "peak_fraction must be greater than 0 and at most 1."
            )

        peak = decoded.image.max()

        threshold = int(
            peak * peak_fraction
        )

        return self.threshold(
            decoded,
            threshold,
        )