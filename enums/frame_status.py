"""
===============================================================================
MPAP

Frame Processing Status Enumeration
===============================================================================
"""

from enum import Enum


class FrameStatus(Enum):
    """
    Indicates what happened while processing a frame.
    """

    PENDING = "PENDING"

    VALID = "VALID"

    BAD_HEADER = "BAD_HEADER"

    DECODE_ERROR = "DECODE_ERROR"

    EMPTY_IMAGE = "EMPTY_IMAGE"

    NO_COMPONENT_FOUND = "NO_COMPONENT_FOUND"

    EMPTY_CONTOUR = "EMPTY_CONTOUR"

    ZERO_AREA = "ZERO_AREA"

    ZERO_INTENSITY = "ZERO_INTENSITY"

    SKIPPED = "SKIPPED"

    ERROR = "ERROR"

    def __str__(self) -> str:
        return self.value