"""
===============================================================================
MPAP
Melt Pool Analysis Platform
===============================================================================

Build State Manager

Maintains the live relationship between processed frames, physical layers,
and the overall build state.

===============================================================================
"""

from models import BuildState, Frame


class BuildStateManager:
    """
    Manages the evolving state of a live additive manufacturing build.

    The manager does not perform image processing or layer detection itself.
    It receives processed frames and explicit layer-transition signals and
    updates the BuildState accordingly.
    """

    def __init__(self, state: BuildState | None = None):
        self.state = state if state is not None else BuildState()

    def add_frame(self, frame: Frame) -> None:
        """Add a processed frame to the current build state."""
        self.state.add_frame(frame)

    def start_new_layer(self) -> None:
        """Complete the current layer and begin a new physical layer."""

        if self.state.current_layer_object is not None:
            self.state.complete_current_layer()

        self.state.start_new_layer()

    def complete_layer(self) -> None:
        """Mark the current layer as complete."""
        self.state.complete_current_layer()

    def mark_idle(self) -> None:
        """Mark the build as idle."""
        self.state.mark_idle()

    def mark_complete(self) -> None:
        """Mark the build as complete."""
        self.state.mark_complete()

    def reset(self) -> None:
        """Reset the manager for a new build."""
        self.state.reset()

    def get_state(self) -> BuildState:
        """Return the current BuildState."""
        return self.state

    @property
    def current_layer(self):
        """Return the current Layer object."""
        return self.state.current_layer_object

    @property
    def current_frame(self) -> int:
        """Return the most recently processed frame index."""
        return self.state.current_frame

    @property
    def current_layer_number(self) -> int:
        """Return the current physical layer number."""
        return self.state.current_layer

    @property
    def frames_processed(self) -> int:
        """Return the total number of processed frames."""
        return self.state.frames_processed

    @property
    def layers_completed(self) -> int:
        """Return the number of completed layers."""
        return self.state.layers_completed

    @property
    def is_active(self) -> bool:
        """Return whether the build is currently active."""
        return self.state.is_active

    @property
    def machine_status(self) -> str:
        """Return the current high-level machine status."""
        return self.state.machine_status
    