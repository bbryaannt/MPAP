"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Transient Event Duration Analysis
===============================================================================

Analyzes transient_events.csv to determine the duration distribution of
classification events.

This is an analysis-only step.

It does NOT modify:
    - the classifier
    - frame classifications
    - layer classifications
    - transient event detection

The purpose is to understand whether transient events naturally separate
into short-lived and sustained behavior before introducing any persistence
rules.
===============================================================================
"""

from pathlib import Path

import pandas as pd


# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)

INPUT_CSV = DATASET / "transient_events.csv"

FRAME_RATE = 60.0


# =============================================================================
# HELPERS
# =============================================================================

def print_header(title: str) -> None:
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * 90)


def duration_category(frames: int) -> str:
    """
    Assign a descriptive duration category.

    These categories are descriptive only.

    They are NOT MPAP classification rules and should not be interpreted
    as scientifically validated thresholds.
    """

    if frames == 1:
        return "1_FRAME"

    if frames == 2:
        return "2_FRAMES"

    if 3 <= frames <= 5:
        return "3_5_FRAMES"

    if 6 <= frames <= 10:
        return "6_10_FRAMES"

    if 11 <= frames <= 30:
        return "11_30_FRAMES"

    if 31 <= frames <= 60:
        return "31_60_FRAMES"

    return "61_PLUS_FRAMES"


def category_order() -> list[str]:
    return [
        "1_FRAME",
        "2_FRAMES",
        "3_5_FRAMES",
        "6_10_FRAMES",
        "11_30_FRAMES",
        "31_60_FRAMES",
        "61_PLUS_FRAMES",
    ]


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def main() -> None:

    print_header(
        "MPAP — TRANSIENT EVENT DURATION ANALYSIS"
    )

    print()
    print(f"Dataset: {DATASET}")
    print(f"Input:   {INPUT_CSV}")

    if not INPUT_CSV.exists():

        print()
        print(
            f"ERROR: Could not find {INPUT_CSV}"
        )

        raise SystemExit(1)

    events_df = pd.read_csv(
        INPUT_CSV
    )

    print()
    print(
        f"Events loaded: {len(events_df)}"
    )

    if events_df.empty:

        print()
        print(
            "No transient events were found."
        )

        return

    required_columns = {
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
    }

    missing = (
        required_columns
        - set(events_df.columns)
    )

    if missing:

        print()
        print(
            "ERROR: Missing required columns:"
        )

        for column in sorted(missing):
            print(
                f"  - {column}"
            )

        raise SystemExit(1)

    # =========================================================================
    # BASIC EVENT SUMMARY
    # =========================================================================

    print_section(
        "OVERALL EVENT DURATION SUMMARY"
    )

    total_events = len(events_df)

    total_frames = int(
        events_df["Duration_Frames"].sum()
    )

    average_duration = float(
        events_df["Duration_Frames"].mean()
    )

    median_duration = float(
        events_df["Duration_Frames"].median()
    )

    minimum_duration = int(
        events_df["Duration_Frames"].min()
    )

    maximum_duration = int(
        events_df["Duration_Frames"].max()
    )

    print(
        f"Total events:          {total_events}"
    )

    print(
        f"Total event frames:    {total_frames}"
    )

    print(
        f"Average duration:      "
        f"{average_duration:.2f} frames"
    )

    print(
        f"Median duration:       "
        f"{median_duration:.2f} frames"
    )

    print(
        f"Minimum duration:      "
        f"{minimum_duration} frame"
    )

    print(
        f"Maximum duration:      "
        f"{maximum_duration} frames"
    )

    print(
        f"Average duration:      "
        f"{average_duration / FRAME_RATE:.4f} seconds"
    )

    print(
        f"Median duration:       "
        f"{median_duration / FRAME_RATE:.4f} seconds"
    )

    print(
        f"Maximum duration:      "
        f"{maximum_duration / FRAME_RATE:.4f} seconds"
    )

    # =========================================================================
    # DURATION DISTRIBUTION
    # =========================================================================

    print_section(
        "EVENT DURATION DISTRIBUTION"
    )

    events_df["Duration_Category"] = (
        events_df["Duration_Frames"]
        .apply(duration_category)
    )

    counts = (
        events_df["Duration_Category"]
        .value_counts()
    )

    for category in category_order():

        event_count = int(
            counts.get(category, 0)
        )

        percentage = (
            event_count
            / total_events
            * 100.0
        )

        print(
            f"{category:<16} "
            f"{event_count:4d} events "
            f"({percentage:6.2f}%)"
        )

    # =========================================================================
    # FRAMES REPRESENTED BY EACH DURATION CATEGORY
    # =========================================================================

    print_section(
        "FRAMES REPRESENTED BY DURATION CATEGORY"
    )

    frame_counts = (
        events_df
        .groupby("Duration_Category")[
            "Duration_Frames"
        ]
        .sum()
    )

    for category in category_order():

        category_frames = int(
            frame_counts.get(category, 0)
        )

        percentage = (
            category_frames
            / total_frames
            * 100.0
        )

        print(
            f"{category:<16} "
            f"{category_frames:5d} frames "
            f"({percentage:6.2f}% of event frames)"
        )

    # =========================================================================
    # EXACT DURATION COUNTS
    # =========================================================================

    print_section(
        "EXACT EVENT DURATION COUNTS"
    )

    exact_counts = (
        events_df["Duration_Frames"]
        .value_counts()
        .sort_index()
    )

    for duration, count in exact_counts.items():

        duration = int(duration)
        count = int(count)

        percentage = (
            count
            / total_events
            * 100.0
        )

        seconds = (
            duration
            / FRAME_RATE
        )

        print(
            f"{duration:4d} frames "
            f"({seconds:7.4f} s): "
            f"{count:4d} events "
            f"({percentage:6.2f}%)"
        )

    # =========================================================================
    # CLASSIFICATION-SPECIFIC DURATIONS
    # =========================================================================

    print_section(
        "DURATION BY CLASSIFICATION"
    )

    classifications = sorted(
        events_df["Classification"]
        .dropna()
        .unique()
    )

    for classification in classifications:

        subset = events_df[
            events_df["Classification"]
            == classification
        ]

        if subset.empty:
            continue

        event_count = len(subset)

        total_class_frames = int(
            subset["Duration_Frames"].sum()
        )

        average = float(
            subset["Duration_Frames"].mean()
        )

        median = float(
            subset["Duration_Frames"].median()
        )

        maximum = int(
            subset["Duration_Frames"].max()
        )

        print()
        print(
            f"{classification}"
        )

        print(
            f"  Events:             {event_count}"
        )

        print(
            f"  Total frames:       {total_class_frames}"
        )

        print(
            f"  Average duration:   "
            f"{average:.2f} frames "
            f"({average / FRAME_RATE:.4f} s)"
        )

        print(
            f"  Median duration:    "
            f"{median:.2f} frames "
            f"({median / FRAME_RATE:.4f} s)"
        )

        print(
            f"  Maximum duration:   "
            f"{maximum} frames "
            f"({maximum / FRAME_RATE:.4f} s)"
        )

    # =========================================================================
    # LOW_POWDER DURATION ANALYSIS
    # =========================================================================

    print_section(
        "LOW_POWDER DURATION ANALYSIS"
    )

    low_powder = events_df[
        events_df["Classification"]
        == "LOW_POWDER"
    ].copy()

    if low_powder.empty:

        print(
            "No LOW_POWDER events detected."
        )

    else:

        lp_events = len(low_powder)

        lp_frames = int(
            low_powder["Duration_Frames"].sum()
        )

        lp_average = float(
            low_powder["Duration_Frames"].mean()
        )

        lp_median = float(
            low_powder["Duration_Frames"].median()
        )

        lp_maximum = int(
            low_powder["Duration_Frames"].max()
        )

        print(
            f"LOW_POWDER events:       {lp_events}"
        )

        print(
            f"LOW_POWDER frames:       {lp_frames}"
        )

        print(
            f"Average duration:        "
            f"{lp_average:.2f} frames "
            f"({lp_average / FRAME_RATE:.4f} s)"
        )

        print(
            f"Median duration:         "
            f"{lp_median:.2f} frames "
            f"({lp_median / FRAME_RATE:.4f} s)"
        )

        print(
            f"Longest duration:        "
            f"{lp_maximum} frames "
            f"({lp_maximum / FRAME_RATE:.4f} s)"
        )

        print()

        print(
            "LOW_POWDER events by duration:"
        )

        lp_counts = (
            low_powder["Duration_Category"]
            .value_counts()
        )

        lp_frame_counts = (
            low_powder
            .groupby("Duration_Category")[
                "Duration_Frames"
            ]
            .sum()
        )

        for category in category_order():

            event_count = int(
                lp_counts.get(category, 0)
            )

            category_frames = int(
                lp_frame_counts.get(category, 0)
            )

            event_percentage = (
                event_count
                / lp_events
                * 100.0
            )

            frame_percentage = (
                category_frames
                / lp_frames
                * 100.0
            )

            print(
                f"  {category:<16} "
                f"{event_count:4d} events "
                f"({event_percentage:6.2f}%) | "
                f"{category_frames:5d} frames "
                f"({frame_percentage:6.2f}%)"
            )

    # =========================================================================
    # LOW_POWDER DURATION BY LAYER
    # =========================================================================

    print_section(
        "LOW_POWDER DURATION BY LAYER"
    )

    if low_powder.empty:

        print("None")

    else:

        layer_summary = (
            low_powder
            .groupby("Layer")
            .agg(
                Events=("Event_ID", "count"),
                Frames=("Duration_Frames", "sum"),
                Average_Duration=(
                    "Duration_Frames",
                    "mean",
                ),
                Median_Duration=(
                    "Duration_Frames",
                    "median",
                ),
                Maximum_Duration=(
                    "Duration_Frames",
                    "max",
                ),
            )
            .reset_index()
            .sort_values("Layer")
        )

        for _, row in layer_summary.iterrows():

            layer = int(
                row["Layer"]
            )

            events = int(
                row["Events"]
            )

            frames = int(
                row["Frames"]
            )

            average = float(
                row["Average_Duration"]
            )

            median = float(
                row["Median_Duration"]
            )

            maximum = int(
                row["Maximum_Duration"]
            )

            print(
                f"L{layer:02d}: "
                f"{events:3d} events | "
                f"{frames:4d} frames | "
                f"avg "
                f"{average:6.2f} | "
                f"median "
                f"{median:6.2f} | "
                f"max "
                f"{maximum:3d}"
            )

    # =========================================================================
    # SUSTAINED LOW_POWDER EVENTS
    # =========================================================================

    print_section(
        "LONGEST LOW_POWDER EVENTS"
    )

    if low_powder.empty:

        print("None")

    else:

        longest = (
            low_powder
            .sort_values(
                "Duration_Frames",
                ascending=False,
            )
            .head(15)
        )

        print(
            f"{'Event':>6} "
            f"{'Layer':>6} "
            f"{'Start':>7} "
            f"{'End':>7} "
            f"{'Frames':>7} "
            f"{'Seconds':>9} "
            f"{'B4':>8} "
            f"{'Area':>8} "
            f"{'Cir':>7}"
        )

        for _, row in longest.iterrows():

            print(
                f"{int(row['Event_ID']):6d} "
                f"{int(row['Layer']):6d} "
                f"{int(row['Start_Frame']):7d} "
                f"{int(row['End_Frame']):7d} "
                f"{int(row['Duration_Frames']):7d} "
                f"{row['Duration_Seconds']:9.4f} "
                f"{row['Mean_Band4']:8.1f} "
                f"{row['Mean_Area_mm2']:8.3f} "
                f"{row['Mean_Circularity']:7.3f}"
            )

    # =========================================================================
    # SHORT LOW_POWDER EVENTS
    # =========================================================================

    print_section(
        "SHORT LOW_POWDER EVENTS"
    )

    if low_powder.empty:

        print("None")

    else:

        short_events = (
            low_powder[
                low_powder["Duration_Frames"]
                <= 5
            ]
            .sort_values(
                [
                    "Layer",
                    "Start_Frame",
                ]
            )
        )

        short_count = len(
            short_events
        )

        short_frames = int(
            short_events["Duration_Frames"].sum()
        )

        percentage_events = (
            short_count
            / len(low_powder)
            * 100.0
        )

        percentage_frames = (
            short_frames
            / int(
                low_powder["Duration_Frames"].sum()
            )
            * 100.0
        )

        print(
            f"LOW_POWDER events <= 5 frames: "
            f"{short_count}"
        )

        print(
            f"LOW_POWDER frames <= 5 frames: "
            f"{short_frames}"
        )

        print(
            f"Percentage of LOW_POWDER events: "
            f"{percentage_events:.2f}%"
        )

        print(
            f"Percentage of LOW_POWDER frames: "
            f"{percentage_frames:.2f}%"
        )

    # =========================================================================
    # LONG LOW_POWDER EVENTS
    # =========================================================================

    print_section(
        "LONG LOW_POWDER EVENTS"
    )

    if low_powder.empty:

        print("None")

    else:

        long_events = (
            low_powder[
                low_powder["Duration_Frames"]
                >= 10
            ]
            .sort_values(
                "Duration_Frames",
                ascending=False,
            )
        )

        long_count = len(
            long_events
        )

        long_frames = int(
            long_events["Duration_Frames"].sum()
        )

        percentage_events = (
            long_count
            / len(low_powder)
            * 100.0
        )

        percentage_frames = (
            long_frames
            / int(
                low_powder["Duration_Frames"].sum()
            )
            * 100.0
        )

        print(
            f"LOW_POWDER events >= 10 frames: "
            f"{long_count}"
        )

        print(
            f"LOW_POWDER frames >= 10 frames: "
            f"{long_frames}"
        )

        print(
            f"Percentage of LOW_POWDER events: "
            f"{percentage_events:.2f}%"
        )

        print(
            f"Percentage of LOW_POWDER frames: "
            f"{percentage_frames:.2f}%"
        )

    # =========================================================================
    # SAVE ENRICHED EVENT CSV
    # =========================================================================

    output_csv = (
        DATASET
        / "transient_events_with_duration_category.csv"
    )

    events_df.to_csv(
        output_csv,
        index=False,
    )

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================

    print_header(
        "DURATION ANALYSIS COMPLETE"
    )

    print()
    print(
        "This analysis did not modify frame classification,"
    )
    print(
        "layer classification, or transient-event detection."
    )

    print()
    print(
        f"Events analyzed: {total_events}"
    )

    print(
        f"Output written to:"
    )

    print(
        f"  {output_csv}"
    )


if __name__ == "__main__":
    main()