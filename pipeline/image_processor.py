"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Image Processor
===============================================================================
"""

import numpy as np

from models import DecodedImage


class RPM222XRImageProcessor:
    """
    Performs basic preprocessing on decoded RPM222XR images.

    The processor does not decode files. It operates only on an already
    decoded uint16 image.
    """

    def normalize(
        self,
        decoded: DecodedImage,
    ) -> np.ndarray:
        """
        Normalize a decoded image to floating-point values between 0 and 1.
        """

        image = decoded.image.astype(np.float32)

        minimum = image.min()
        maximum = image.max()

        if maximum == minimum:
            return np.zeros_like(image, dtype=np.float32)

        normalized = (
            image - minimum
        ) / (
            maximum - minimum
        )

        return normalized

    def clip(
        self,
        decoded: DecodedImage,
        low: int,
        high: int,
    ) -> np.ndarray:
        """
        Clip image values to a specified intensity range.
        """

        if low >= high:
            raise ValueError(
                "low must be less than high."
            )

        return np.clip(
            decoded.image,
            low,
            high,
        )

    def threshold(
        self,
        decoded: DecodedImage,
        value: int,
    ) -> np.ndarray:
        """
        Create a binary mask from an intensity threshold.
        """

        return decoded.image >= value