"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Live Layer Tracker
===============================================================================

Tracks incoming frame classifications and detects physical layer boundaries
from sustained LASER_OFF periods.

A sustained LASER_OFF period is treated as a potential layer boundary.

A new layer is only confirmed when an active frame appears AFTER the
LASER_OFF threshold has been reached.

This prevents the final machine shutdown from being incorrectly counted as
an additional layer.

===============================================================================
"""

from pipeline.classifier import MeltPoolClassification


class LayerTracker:
    """
    Tracks frame classifications and detects layer transitions.

    Layer detection works as follows:

        ACTIVE
           ↓
        LASER_OFF
           ↓
        sustained LASER_OFF threshold
           ↓
        WAITING FOR NEXT ACTIVE FRAME
           ↓
        active frame
           ↓
        NEW LAYER

    Initial LASER_OFF frames before the first active frame are ignored.

    A final LASER_OFF period at the end of a build does not create a new
    layer unless another active frame follows it.

    Parameters
    ----------
    laser_off_threshold : int
        Number of consecutive LASER_OFF frames required to identify a
        potential layer boundary.
    """

    def __init__(
        self,
        laser_off_threshold: int = 120,
    ):
        if laser_off_threshold <= 0:
            raise ValueError(
                "laser_off_threshold must be greater than 0."
            )

        self.laser_off_threshold = laser_off_threshold

        self._laser_off_count = 0
        self._layer_complete = False
        self._has_seen_active_frame = False

    def update(
        self,
        classification: MeltPoolClassification,
    ) -> bool:
        """
        Process one frame classification.

        Returns
        -------
        bool
            True when an active frame begins a new layer after a sustained
            LASER_OFF period.

        Important
        ---------
        The transition is reported on the FIRST ACTIVE frame after the
        sustained LASER_OFF period.

        This means a trailing LASER_OFF period at the end of a build does
        not create a phantom final layer.
        """

        is_laser_off = (
            classification == MeltPoolClassification.LASER_OFF
        )

        # ------------------------------------------------------------------
        # LASER OFF
        # ------------------------------------------------------------------

        if is_laser_off:

            # Initial LASER_OFF frames before the first active frame are
            # pre-build / initialization frames and do not count toward
            # layer transitions.
            if not self._has_seen_active_frame:
                self._laser_off_count = 0
                self._layer_complete = False
                return False

            self._laser_off_count += 1

            # Once the threshold is reached, mark the current layer as
            # potentially complete.
            #
            # We intentionally DO NOT return True here.
            #
            # We need to see an active frame afterward to prove that another
            # layer actually exists.
            if self._laser_off_count >= self.laser_off_threshold:
                self._layer_complete = True

            return False

        # ------------------------------------------------------------------
        # ACTIVE FRAME
        # ------------------------------------------------------------------

        was_layer_complete = self._layer_complete

        # This is now definitely an active process frame.
        self._has_seen_active_frame = True

        # If a sustained LASER_OFF period preceded this active frame,
        # this frame belongs to the NEW layer.
        layer_transition = (
            was_layer_complete
            and self._laser_off_count >= self.laser_off_threshold
        )

        # Reset the OFF tracking for the new active layer.
        self._laser_off_count = 0
        self._layer_complete = False

        return layer_transition

    def reset(self) -> None:
        """
        Reset the tracker for a new build.
        """

        self._laser_off_count = 0
        self._layer_complete = False
        self._has_seen_active_frame = False

    @property
    def laser_off_count(self) -> int:
        """Number of consecutive LASER_OFF frames."""

        return self._laser_off_count

    @property
    def layer_complete(self) -> bool:
        """
        Whether the current layer has entered a sustained LASER_OFF state.

        This indicates a potential completed layer, not necessarily a confirmed
        transition to another layer.
        """

        return self._layer_complete

    @property
    def has_seen_active_frame(self) -> bool:
        """Whether an active process frame has been observed."""

        return self._has_seen_active_frame