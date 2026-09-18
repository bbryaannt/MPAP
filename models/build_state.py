"""
===============================================================================
MPAP
Melt Pool Analysis Platform
===============================================================================

Live Build State Model

Represents the current state of an MPAP-monitored additive manufacturing
build.

===============================================================================
"""

from dataclasses import dataclass, field
from typing import Optional

from models import Frame, Layer


@dataclass(slots=True)
class BuildState:
    """
    Represents the current state of a live additive manufacturing build.

    BuildState is intentionally responsible for process state, not for
    performing image processing, classification, anomaly detection, or
    machine control.

    Those responsibilities belong to other parts of MPAP.

    Attributes
    ----------
    current_frame : int
        Global index of the most recently processed frame.

    current_layer : int
        Index of the physical layer currently being processed.

    frames_processed : int
        Total number of frames successfully processed.

    layers_completed : int
        Number of physical layers that have been completed.

    layers : list[Layer]
        Physical layers accumulated during the build.

    is_active : bool
        Whether MPAP currently considers the build to be actively printing.

    machine_status : str
        Current high-level machine/build status.

    last_frame : Frame | None
        Most recently processed frame.

    """

    current_frame: int = 0
    current_layer: int = 0

    frames_processed: int = 0
    layers_completed: int = 0

    layers: list[Layer] = field(default_factory=list)

    is_active: bool = False
    machine_status: str = "IDLE"

    last_frame: Optional[Frame] = None

    def add_frame(self, frame: Frame) -> None:
        """
        Add a processed frame to the current build state.

        The frame is assigned to the current layer. Layer creation and
        transitions will eventually be controlled by MPAP's layer-detection
        system.
        """

        self.last_frame = frame
        self.current_frame = frame.index
        self.frames_processed += 1

        if not self.layers:
            self.current_layer = 1
            self.layers.append(
                Layer(index=self.current_layer)
            )

        self.layers[-1].add_frame(frame)

        self.is_active = True
        self.machine_status = "PROCESSING"

    def start_new_layer(self) -> Layer:
        """
        Create and begin tracking a new physical layer.

        Returns
        -------
        Layer
            The newly created layer.
        """

        self.current_layer += 1

        layer = Layer(index=self.current_layer)
        self.layers.append(layer)

        self.layers_completed = max(
            0,
            len(self.layers) - 1,
        )

        return layer

    def complete_current_layer(self) -> None:
        """
        Mark the current layer as completed.
        """

        if not self.layers:
            return

        self.layers_completed = len(self.layers)

    def mark_idle(self) -> None:
        """
        Mark the build as currently idle.
        """

        self.is_active = False
        self.machine_status = "IDLE"

    def mark_complete(self) -> None:
        """
        Mark the build as complete.
        """

        self.is_active = False
        self.machine_status = "COMPLETE"

        if self.layers:
            self.layers_completed = len(self.layers)

    def reset(self) -> None:
        """
        Reset the build state for a new build.
        """

        self.current_frame = 0
        self.current_layer = 0

        self.frames_processed = 0
        self.layers_completed = 0

        self.layers.clear()

        self.is_active = False
        self.machine_status = "IDLE"

        self.last_frame = None

    @property
    def current_layer_object(self) -> Optional[Layer]:
        """
        Return the currently active Layer object.

        Returns None if no layer has been created yet.
        """

        if not self.layers:
            return None

        return self.layers[-1]

    @property
    def total_layers(self) -> int:
        """
        Return the number of layers currently tracked.
        """

        return len(self.layers)

    @property
    def current_layer_frame_count(self) -> int:
        """
        Return the number of frames in the current layer.
        """

        layer = self.current_layer_object

        if layer is None:
            return 0

        return layer.frame_count