"""
===============================================================================
MPAP

Build Model

Represents one additive manufacturing build.
===============================================================================
"""

from dataclasses import dataclass, field
from pathlib import Path

from models import Layer


@dataclass(slots=True)
class Build:
    """
    Represents one complete additive manufacturing build.
    """

    name: str

    path: Path

    layers: list[Layer] = field(default_factory=list)

    @property
    def layer_count(self) -> int:
        """Number of physical layers."""
        return len(self.layers)

    @property
    def frame_count(self) -> int:
        """Total number of frames."""
        return sum(
            layer.frame_count
            for layer in self.layers
        )

    @property
    def measured_frame_count(self) -> int:
        """Frames with valid measurements."""
        return sum(
            layer.measured_frame_count
            for layer in self.layers
        )

    @property
    def first_layer(self) -> Layer | None:

        if not self.layers:
            return None

        return self.layers[0]

    @property
    def last_layer(self) -> Layer | None:

        if not self.layers:
            return None

        return self.layers[-1]

    def add_layer(self, layer: Layer) -> None:
        """
        Add one physical layer.
        """

        if self.layers:

            if layer.index <= self.layers[-1].index:

                raise ValueError(
                    "Layers must be added in ascending order."
                )

        self.layers.append(layer)