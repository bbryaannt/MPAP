"""
===============================================================================
MPAP

Frame Model

Represents a single decoded camera frame.
===============================================================================
"""

from dataclasses import dataclass
from pathlib import Path

from enums import FrameStatus
from models import Measurement


@dataclass(frozen=True, slots=True)
class Frame:
    """
    Represents one frame acquired by the camera.

    Parameters
    ----------
    index : int
        Zero-based frame number.

    path : Path
        Path to the original .dat file.

    status : FrameStatus
        Processing status of this frame.

    measurement : Measurement | None
        Melt pool measurement extracted from this frame.
        None if no valid measurement exists.
    """

    index: int

    path: Path

    status: FrameStatus

    measurement: Measurement | None = None

    @property
    def has_measurement(self) -> bool:
        """Return True if this frame contains a valid measurement."""
        return self.measurement is not None

    @property
    def filename(self) -> str:
        """Return only the filename."""
        return self.path.name

    @property
    def stem(self) -> str:
        """Filename without extension."""
        return self.path.stem