"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Decoded Image Model

Represents a decoded RPM222XR .dat file.
===============================================================================
"""

from dataclasses import dataclass
import numpy as np

from models.header import Header


@dataclass(frozen=True, slots=True)
class DecodedImage:
    """
    Represents a decoded thermal image.
    """

    image: np.ndarray

    header: Header

    @property
    def width(self):
        return self.header.width

    @property
    def height(self):
        return self.header.height

    @property
    def bit_depth(self):
        return self.header.bit_depth

    @property
    def pixel_format(self):
        return self.header.pixel_format

    @property
    def schema(self):
        return self.header.schema

    @property
    def header_size(self):
        return self.header.header_size

    @property
    def shape(self):
        return self.image.shape

    @property
    def dtype(self):
        return self.image.dtype

    def __str__(self):
        return (
            "DecodedImage("
            f"{self.width}x{self.height}, "
            f"{self.bit_depth}-bit, "
            f"schema={self.schema})"
        )