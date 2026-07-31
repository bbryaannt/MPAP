"""
===============================================================================
MPAP
Melt Pool Analysis Platform

RPM222XR Header Model
===============================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Header:
    """
    Represents an RPM222XR file header.
    """

    schema: int

    width: int
    height: int

    bit_depth: int

    pixel_format: int

    header_size: int

    raw_bytes: bytes

    header_length_words: int | None = None

    @property
    def image_shape(self) -> tuple[int, int]:
        return (self.height, self.width)

    @property
    def pixel_count(self) -> int:
        return self.width * self.height

    def __str__(self) -> str:
        return (
            "Header("
            f"schema={self.schema}, "
            f"{self.width}x{self.height}, "
            f"{self.bit_depth}-bit)"
        )