"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Transient Event Detection
===============================================================================

Groups consecutive frame classifications into transient events.

This module does NOT change frame classifications.

It answers a different question:

    "When a classification occurs, how long does it persist?"

Laser-off periods are treated as boundaries between active layers.

A layer is incremented only when the data transitions from a LASER_OFF
period into a new active period.

Example:

    LASER_OFF
    LASER_OFF
    LOW_POWER
    LOW_POWER
    LOW_POWDER
    LOW_POWDER
    LOW_POWER
    LASER_OFF
    LASER_OFF
    LOW_POWER

becomes:

    Layer 1:
        LOW_POWER event
        LOW_POWDER event
        LOW_POWER event

    Layer 2:
        LOW_POWER event
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class TransientEvent:
    """
    A consecutive run of one non-LASER_OFF classification.
    """

    event_id: int
    layer: int
    classification: str

    start_frame: int
    end_frame: int
    duration_frames: int

    mean_area_mm2: float
    mean_circularity: float
    mean_aspect_ratio: float

    mean_band3: float
    mean_band4: float
    mean_band5: float

    duration_seconds: float


class TransientEventDetector:
    """
    Detect consecutive classification runs within active laser sections.

    A transient event is a consecutive run of the same classification.

    LASER_OFF frames define the boundaries between active layers.

    Important:
        A long sequence of LASER_OFF frames represents one inactive period,
        not one new layer per frame.
    """

    REQUIRED_COLUMNS = {
        "Frame",
        "Classification",
        "Area_mm2",
        "Circularity",
        "Aspect_Ratio",
        "Band3",
        "Band4",
        "Band5",
    }

    def __init__(
        self,
        frame_rate: float = 60.0,
        ignored_classifications: Optional[set[str]] = None,
    ):
        if frame_rate <= 0:
            raise ValueError(
                "frame_rate must be greater than 0."
            )

        self.frame_rate = frame_rate

        self.ignored_classifications = (
            ignored_classifications
            if ignored_classifications is not None
            else {"LASER_OFF"}
        )

    def detect(
        self,
        diagnostic_df: pd.DataFrame,
    ) -> list[TransientEvent]:
        """
        Detect consecutive classification runs within active layers.

        A new layer begins when an active frame appears after a LASER_OFF
        period.

        Parameters
        ----------
        diagnostic_df:
            DataFrame containing classification diagnostic data.

        Returns
        -------
        list[TransientEvent]
            Detected classification events.
        """

        self._validate_columns(diagnostic_df)

        if diagnostic_df.empty:
            return []

        df = (
            diagnostic_df
            .copy()
            .sort_values("Frame")
            .reset_index(drop=True)
        )

        events: list[TransientEvent] = []

        event_id = 0
        layer_number = 0

        current_rows: list[pd.Series] = []
        current_classification: Optional[str] = None

        # Tracks whether we are currently inside an active laser section.
        in_active_layer = False

        for _, row in df.iterrows():

            classification = str(
                row["Classification"]
            )

            # -----------------------------------------------------------
            # LASER_OFF / ignored classification
            # -----------------------------------------------------------

            if classification in self.ignored_classifications:

                # Finish the current event if one is active.
                if current_rows:

                    event_id += 1

                    events.append(
                        self._build_event(
                            event_id=event_id,
                            layer=layer_number,
                            rows=current_rows,
                            classification=current_classification,
                        )
                    )

                    current_rows = []
                    current_classification = None

                # Mark that we are now outside the active layer.
                #
                # IMPORTANT:
                # We do NOT increment layer_number here.
                #
                # A sequence of 200 LASER_OFF frames is one boundary,
                # not 200 layers.
                in_active_layer = False

                continue

            # -----------------------------------------------------------
            # First active frame after LASER_OFF
            # -----------------------------------------------------------

            if not in_active_layer:

                layer_number += 1
                in_active_layer = True

                current_classification = classification
                current_rows = [row]

                continue

            # -----------------------------------------------------------
            # Same classification continues the event
            # -----------------------------------------------------------

            if classification == current_classification:

                current_rows.append(row)

                continue

            # -----------------------------------------------------------
            # Classification changed
            # -----------------------------------------------------------

            event_id += 1

            events.append(
                self._build_event(
                    event_id=event_id,
                    layer=layer_number,
                    rows=current_rows,
                    classification=current_classification,
                )
            )

            current_rows = [row]
            current_classification = classification

        # ---------------------------------------------------------------
        # Finish event at EOF
        # ---------------------------------------------------------------

        if current_rows:

            event_id += 1

            events.append(
                self._build_event(
                    event_id=event_id,
                    layer=layer_number,
                    rows=current_rows,
                    classification=current_classification,
                )
            )

        return events

    def to_dataframe(
        self,
        events: list[TransientEvent],
    ) -> pd.DataFrame:
        """
        Convert detected events to a DataFrame.
        """

        columns = [
            "Event_ID",
            "Layer",
            "Classification",
            "Start_Frame",
            "End_Frame",
            "Duration_Frames",
            "Duration_Seconds",
            "Mean_Area_mm2",
            "Mean_Circularity",
            "Mean_Aspect_Ratio",
            "Mean_Band3",
            "Mean_Band4",
            "Mean_Band5",
        ]

        if not events:
            return pd.DataFrame(
                columns=columns
            )

        rows = []

        for event in events:

            rows.append(
                {
                    "Event_ID": event.event_id,
                    "Layer": event.layer,
                    "Classification": event.classification,
                    "Start_Frame": event.start_frame,
                    "End_Frame": event.end_frame,
                    "Duration_Frames": event.duration_frames,
                    "Duration_Seconds": event.duration_seconds,
                    "Mean_Area_mm2": event.mean_area_mm2,
                    "Mean_Circularity": event.mean_circularity,
                    "Mean_Aspect_Ratio": event.mean_aspect_ratio,
                    "Mean_Band3": event.mean_band3,
                    "Mean_Band4": event.mean_band4,
                    "Mean_Band5": event.mean_band5,
                }
            )

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    def _build_event(
        self,
        event_id: int,
        layer: int,
        rows: list[pd.Series],
        classification: Optional[str],
    ) -> TransientEvent:
        """
        Build one TransientEvent from a consecutive group of frames.
        """

        if not rows:
            raise ValueError(
                "Cannot build an event from zero rows."
            )

        if classification is None:
            raise ValueError(
                "Event classification cannot be None."
            )

        data = pd.DataFrame(rows)

        duration_frames = len(data)

        return TransientEvent(
            event_id=event_id,
            layer=layer,
            classification=classification,
            start_frame=int(
                data["Frame"].iloc[0]
            ),
            end_frame=int(
                data["Frame"].iloc[-1]
            ),
            duration_frames=duration_frames,
            mean_area_mm2=float(
                data["Area_mm2"].mean()
            ),
            mean_circularity=float(
                data["Circularity"].mean()
            ),
            mean_aspect_ratio=float(
                data["Aspect_Ratio"].mean()
            ),
            mean_band3=float(
                data["Band3"].mean()
            ),
            mean_band4=float(
                data["Band4"].mean()
            ),
            mean_band5=float(
                data["Band5"].mean()
            ),
            duration_seconds=(
                duration_frames / self.frame_rate
            ),
        )

    def _validate_columns(
        self,
        diagnostic_df: pd.DataFrame,
    ) -> None:
        """
        Validate that the diagnostic CSV contains the required columns.
        """

        missing = (
            self.REQUIRED_COLUMNS
            - set(diagnostic_df.columns)
        )

        if missing:
            raise ValueError(
                "Diagnostic CSV is missing required columns: "
                + ", ".join(sorted(missing))
            )


def detect_transient_events(
    diagnostic_df: pd.DataFrame,
    frame_rate: float = 60.0,
) -> pd.DataFrame:
    """
    Convenience function for detecting transient events.
    """

    detector = TransientEventDetector(
        frame_rate=frame_rate
    )

    events = detector.detect(
        diagnostic_df
    )

    return detector.to_dataframe(
        events
    )
