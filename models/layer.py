"""
===============================================================================
MPAP

Layer Model

Represents one physical layer of an additive manufacturing build.
===============================================================================
"""

from dataclasses import dataclass, field

from models import Frame
from models import LayerStatistics


@dataclass(slots=True)
class Layer:
    """
    Represents one physical layer of a build.
    """

    index: int

    frames: list[Frame] = field(default_factory=list)

    statistics: LayerStatistics | None = None

    @property
    def frame_count(self) -> int:
        """Total number of frames."""
        return len(self.frames)

    @property
    def measured_frame_count(self) -> int:
        """Number of frames containing a valid measurement."""
        return sum(
            frame.has_measurement
            for frame in self.frames
        )

    @property
    def start_frame(self) -> int | None:
        """First global frame index."""
        if not self.frames:
            return None

        return self.frames[0].index

    @property
    def end_frame(self) -> int | None:
        """Last global frame index."""
        if not self.frames:
            return None

        return self.frames[-1].index

    @property
    def duration(self) -> int:
        """
        Number of frame intervals contained in this layer.
        """
        if self.frame_count <= 1:
            return 0

        start = self.start_frame
        end = self.end_frame

        assert start is not None
        assert end is not None

        return end - start

    def add_frame(self, frame: Frame) -> None:
        """
        Add one frame to this layer.
        """
        self.frames.append(frame)