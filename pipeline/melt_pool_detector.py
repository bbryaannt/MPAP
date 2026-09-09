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

    Detection uses two conditions:

    1. The ROI peak must exceed an absolute thermal minimum.
    2. Enough pixels must reach the relative peak threshold.

    This prevents warm background/cooling frames from being interpreted
    as melt pools simply because their background intensity is relatively
    uniform.
    """

    def __init__(
        self,
        roi_half_height: int = 120,
        roi_half_width: int = 250,
        minimum_signal_pixels: int = 100,
        minimum_peak_intensity: int = 35000,
    ):
        self.roi_half_height = roi_half_height
        self.roi_half_width = roi_half_width
        self.minimum_signal_pixels = minimum_signal_pixels
        self.minimum_peak_intensity = minimum_peak_intensity

    def create_roi_mask(
        self,
        decoded: DecodedImage,
    ) -> np.ndarray:
        """
        Create a rectangular ROI centered on the image.
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

    def has_thermal_signal(
        self,
        decoded: DecodedImage,
        peak_fraction: float = 0.85,
    ) -> bool:
        """
        Determine whether a frame contains a meaningful melt-pool signal.

        A frame must satisfy BOTH:

        - ROI peak >= minimum_peak_intensity
        - At least minimum_signal_pixels reach the relative threshold

        The absolute peak requirement prevents background/cooling frames
        from generating a full-ROI mask.
        """

        if not 0 < peak_fraction <= 1:
            raise ValueError(
                "peak_fraction must be greater than 0 and at most 1."
            )

        roi_mask = self.create_roi_mask(decoded)

        roi_pixels = decoded.image[roi_mask]

        if roi_pixels.size == 0:
            return False

        peak = int(roi_pixels.max())

        # ---------------------------------------------------------------
        # Absolute thermal signal check
        # ---------------------------------------------------------------

        if peak < self.minimum_peak_intensity:
            return False

        # ---------------------------------------------------------------
        # Relative thermal signal check
        # ---------------------------------------------------------------

        threshold = int(
            peak * peak_fraction
        )

        signal_mask = (
            decoded.image >= threshold
        ) & roi_mask

        signal_pixel_count = int(
            np.count_nonzero(signal_mask)
        )

        return (
            signal_pixel_count
            >= self.minimum_signal_pixels
        )

    def threshold(
        self,
        decoded: DecodedImage,
        threshold: int,
    ) -> np.ndarray:
        """
        Detect pixels at or above the specified intensity threshold.

        Processing is restricted to the melt-pool ROI.
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
        Detect the melt pool using a fraction of the ROI peak intensity.

        If the frame does not contain a sufficiently strong thermal signal,
        an empty mask is returned.
        """

        if not 0 < peak_fraction <= 1:
            raise ValueError(
                "peak_fraction must be greater than 0 and at most 1."
            )

        # ---------------------------------------------------------------
        # Check for meaningful melt-pool signal
        # ---------------------------------------------------------------

        if not self.has_thermal_signal(
            decoded,
            peak_fraction=peak_fraction,
        ):
            return np.zeros(
                (decoded.height, decoded.width),
                dtype=bool,
            )

        # ---------------------------------------------------------------
        # Determine relative threshold
        # ---------------------------------------------------------------

        roi_mask = self.create_roi_mask(decoded)

        roi_pixels = decoded.image[roi_mask]

        peak = int(roi_pixels.max())

        threshold = int(
            peak * peak_fraction
        )

        # ---------------------------------------------------------------
        # Generate final melt-pool mask
        # ---------------------------------------------------------------

        return self.threshold(
            decoded,
            threshold,
        )