"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Analysis Run Model

Represents one complete MPAP analysis session consisting of one or more builds.
===============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime

from models.build import Build


@dataclass(slots=True)
class AnalysisRun:
    """
    Represents a complete MPAP analysis run.

    An analysis run is the highest-level object in MPAP and groups together
    one or more builds that belong to the same experiment, validation study,
    or research session.
    """

    name: str
    description: str = ""

    created_at: datetime = field(default_factory=datetime.now)

    builds: list[Build] = field(default_factory=list)

    @property
    def build_count(self) -> int:
        """Number of builds contained in this analysis run."""
        return len(self.builds)

    @property
    def layer_count(self) -> int:
        """Total number of layers across every build."""
        return sum(
            build.layer_count
            for build in self.builds
        )

    @property
    def frame_count(self) -> int:
        """Total number of frames across every build."""
        return sum(
            build.frame_count
            for build in self.builds
        )

    @property
    def measured_frame_count(self) -> int:
        """Total number of successfully measured frames."""
        return sum(
            build.measured_frame_count
            for build in self.builds
        )

    def add_build(self, build: Build) -> None:
        """
        Add a build to this analysis run.
        """
        self.builds.append(build)

    def __str__(self) -> str:
        """
        Human-readable summary used when printing an AnalysisRun.
        """
        return (
            "AnalysisRun("
            f"name='{self.name}', "
            f"builds={self.build_count}, "
            f"layers={self.layer_count}, "
            f"frames={self.frame_count}, "
            f"measured_frames={self.measured_frame_count}"
            ")"
        )

   