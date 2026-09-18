"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Transient Event Analysis
===============================================================================

Reads classification_diagnostic.csv and produces transient_events.csv.

This is an additive analysis step.

It does not modify the existing classifier or layer classification.
===============================================================================
"""

from pathlib import Path

import pandas as pd

from pipeline.transient_events import (
    TransientEventDetector,
)


DATASET = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)

INPUT_CSV = DATASET / "classification_diagnostic.csv"
OUTPUT_CSV = DATASET / "transient_events.csv"

FRAME_RATE = 60.0


def main():

    print("=" * 90)
    print("MPAP — TRANSIENT EVENT ANALYSIS")
    print("=" * 90)
    print()

    print(f"Dataset: {DATASET}")
    print(f"Input:   {INPUT_CSV}")
    print()

    if not INPUT_CSV.exists():

        print(
            f"ERROR: Could not find {INPUT_CSV}"
        )

        raise SystemExit(1)

    diagnostic_df = pd.read_csv(
        INPUT_CSV
    )

    print(
        f"Diagnostic frames: {len(diagnostic_df)}"
    )

    detector = TransientEventDetector(
        frame_rate=FRAME_RATE
    )

    events = detector.detect(
        diagnostic_df
    )

    events_df = detector.to_dataframe(
        events
    )

    events_df.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print(
        f"Events detected:   {len(events_df)}"
    )

    print()

    if events_df.empty:

        print(
            "No classification events were detected."
        )

        print()
        print(
            f"Output written to: {OUTPUT_CSV}"
        )

        return

    print("EVENT SUMMARY")
    print("-" * 90)

    classification_counts = (
        events_df["Classification"]
        .value_counts()
    )

    for classification, count in classification_counts.items():

        subset = events_df[
            events_df["Classification"]
            == classification
        ]

        total_frames = int(
            subset["Duration_Frames"].sum()
        )

        average_duration = float(
            subset["Duration_Frames"].mean()
        )

        print(
            f"{classification:<12} "
            f"{count:4d} events | "
            f"{total_frames:5d} frames | "
            f"avg duration {average_duration:6.2f} frames"
        )

    print()

    print("LOW_POWDER EVENT SUMMARY")
    print("-" * 90)

    low_powder = events_df[
        events_df["Classification"]
        == "LOW_POWDER"
    ]

    if low_powder.empty:

        print(
            "No LOW_POWDER events detected."
        )

    else:

        print(
            f"Events:              {len(low_powder)}"
        )

        print(
            f"Total frames:        "
            f"{int(low_powder['Duration_Frames'].sum())}"
        )

        print(
            f"Average duration:    "
            f"{low_powder['Duration_Frames'].mean():.2f} frames"
        )

        print(
            f"Longest event:       "
            f"{int(low_powder['Duration_Frames'].max())} frames"
        )

        print(
            f"Average B4:          "
            f"{low_powder['Mean_Band4'].mean():.1f}"
        )

        print(
            f"Average area:        "
            f"{low_powder['Mean_Area_mm2'].mean():.3f} mm²"
        )

        print(
            f"Average circularity: "
            f"{low_powder['Mean_Circularity'].mean():.3f}"
        )

    print()

    print("LOW_POWDER EVENTS BY LAYER")
    print("-" * 90)

    if low_powder.empty:

        print("None")

    else:

        by_layer = (
            low_powder
            .groupby("Layer")
            .agg(
                Events=("Event_ID", "count"),
                Frames=("Duration_Frames", "sum"),
                Average_Duration=("Duration_Frames", "mean"),
                Average_B4=("Mean_Band4", "mean"),
                Average_Area=("Mean_Area_mm2", "mean"),
                Average_Circularity=(
                    "Mean_Circularity",
                    "mean",
                ),
            )
            .reset_index()
        )

        for _, row in by_layer.iterrows():

            print(
                f"L{int(row['Layer']):02d}: "
                f"{int(row['Events']):3d} events | "
                f"{int(row['Frames']):3d} frames | "
                f"avg duration "
                f"{row['Average_Duration']:5.2f} | "
                f"B4 "
                f"{row['Average_B4']:6.1f} | "
                f"area "
                f"{row['Average_Area']:5.2f} | "
                f"cir "
                f"{row['Average_Circularity']:.3f}"
            )

    print()
    print("=" * 90)
    print(
        f"Output written to: {OUTPUT_CSV}"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()
