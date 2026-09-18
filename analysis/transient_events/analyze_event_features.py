"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Transient Event Feature Analysis
===============================================================================

Analyzes the relationship between transient-event duration and the underlying
melt-pool features.

This script is intentionally exploratory.

It does NOT:
    - modify the classifier
    - modify transient-event detection
    - apply persistence filtering
    - change any existing MPAP outputs

The goal is to determine whether event duration corresponds to meaningful
differences in melt-pool behavior.

Input:
    transient_events.csv

Output:
    transient_event_feature_analysis.csv
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

OUTPUT_CSV = (
    DATASET / "transient_event_feature_analysis.csv"
)


# =============================================================================
# HELPERS
# =============================================================================

def print_header(title):
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


def print_section(title):
    print()
    print("-" * 90)
    print(title)
    print("-" * 90)


def format_number(value, decimals=2):

    if pd.isna(value):
        return "N/A"

    return f"{value:.{decimals}f}"


def duration_category(duration):

    duration = int(duration)

    if duration == 1:
        return "1_FRAME"

    if duration == 2:
        return "2_FRAMES"

    if 3 <= duration <= 5:
        return "3_5_FRAMES"

    if 6 <= duration <= 10:
        return "6_10_FRAMES"

    if 11 <= duration <= 30:
        return "11_30_FRAMES"

    if 31 <= duration <= 60:
        return "31_60_FRAMES"

    return "61_PLUS_FRAMES"


# =============================================================================
# FEATURE DEFINITIONS
# =============================================================================

FEATURE_COLUMNS = [
    "Mean_Band3",
    "Mean_Band4",
    "Mean_Band5",
    "Mean_Area_mm2",
    "Mean_Circularity",
    "Mean_Aspect_Ratio",
]


DISPLAY_NAMES = {
    "Mean_Band3": "Band 3",
    "Mean_Band4": "Band 4",
    "Mean_Band5": "Band 5",
    "Mean_Area_mm2": "Area",
    "Mean_Circularity": "Circularity",
    "Mean_Aspect_Ratio": "Aspect ratio",
}


DURATION_ORDER = [
    "1_FRAME",
    "2_FRAMES",
    "3_5_FRAMES",
    "6_10_FRAMES",
    "11_30_FRAMES",
    "31_60_FRAMES",
    "61_PLUS_FRAMES",
]


CLASSIFICATION_ORDER = [
    "GOOD",
    "LOW_POWDER",
    "LOW_POWER",
    "HIGH_POWER",
    "UNKNOWN",
]


# =============================================================================
# MAIN
# =============================================================================

def main():

    print_header(
        "MPAP — TRANSIENT EVENT FEATURE ANALYSIS"
    )

    print()
    print(f"Dataset: {DATASET}")
    print(f"Input:   {INPUT_CSV}")
    print()

    if not INPUT_CSV.exists():

        print(
            f"ERROR: Could not find {INPUT_CSV}"
        )

        raise SystemExit(1)

    # =========================================================================
    # LOAD DATA
    # =========================================================================

    events_df = pd.read_csv(
        INPUT_CSV
    )

    print(
        f"Events loaded: {len(events_df)}"
    )

    if events_df.empty:

        print()
        print(
            "No events were found."
        )

        return

    # =========================================================================
    # CHECK REQUIRED COLUMNS
    # =========================================================================

    required_columns = [
        "Event_ID",
        "Layer",
        "Classification",
        "Duration_Frames",
        "Duration_Seconds",
        *FEATURE_COLUMNS,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in events_df.columns
    ]

    if missing_columns:

        print()
        print(
            "ERROR: Missing required columns:"
        )

        for column in missing_columns:
            print(
                f"  - {column}"
            )

        raise SystemExit(1)

    # =========================================================================
    # CREATE DURATION CATEGORY
    # =========================================================================

    events_df["Duration_Category"] = (
        events_df["Duration_Frames"]
        .apply(duration_category)
    )

    # =========================================================================
    # EVENTS BY DURATION
    # =========================================================================

    print_section(
        "EVENTS BY DURATION CATEGORY"
    )

    for category in DURATION_ORDER:

        subset = events_df[
            events_df["Duration_Category"]
            == category
        ]

        if subset.empty:
            continue

        print(
            f"{category:<16} "
            f"{len(subset):4d} events | "
            f"avg duration "
            f"{subset['Duration_Frames'].mean():6.2f} frames"
        )

    # =========================================================================
    # FEATURE SUMMARY BY DURATION
    # =========================================================================

    print_section(
        "FEATURES BY EVENT DURATION"
    )

    summary_rows = []

    for category in DURATION_ORDER:

        subset = events_df[
            events_df["Duration_Category"]
            == category
        ]

        if subset.empty:
            continue

        print()
        print(category)
        print(
            f"Events: {len(subset)}"
        )

        row = {
            "Duration_Category": category,
            "Events": len(subset),
            "Mean_Duration_Frames": (
                subset["Duration_Frames"].mean()
            ),
            "Median_Duration_Frames": (
                subset["Duration_Frames"].median()
            ),
        }

        for column in FEATURE_COLUMNS:

            mean_value = subset[column].mean()
            median_value = subset[column].median()

            row[
                f"{column}_Mean"
            ] = mean_value

            row[
                f"{column}_Median"
            ] = median_value

            print(
                f"  {DISPLAY_NAMES[column]:<18} "
                f"mean {format_number(mean_value, 3):>10} | "
                f"median {format_number(median_value, 3):>10}"
            )

        summary_rows.append(row)

    # =========================================================================
    # FEATURE SUMMARY BY CLASSIFICATION
    # =========================================================================

    print_section(
        "FEATURES BY CLASSIFICATION"
    )

    classification_rows = []

    for classification in CLASSIFICATION_ORDER:

        subset = events_df[
            events_df["Classification"]
            == classification
        ]

        if subset.empty:
            continue

        print()
        print(classification)

        print(
            f"Events: {len(subset)}"
        )

        print(
            f"Average duration: "
            f"{subset['Duration_Frames'].mean():.2f} frames"
        )

        print(
            f"Median duration:  "
            f"{subset['Duration_Frames'].median():.2f} frames"
        )

        row = {
            "Classification": classification,
            "Events": len(subset),
            "Mean_Duration_Frames": (
                subset["Duration_Frames"].mean()
            ),
            "Median_Duration_Frames": (
                subset["Duration_Frames"].median()
            ),
        }

        for column in FEATURE_COLUMNS:

            value = subset[column].mean()

            row[
                f"{column}_Mean"
            ] = value

            print(
                f"  {DISPLAY_NAMES[column]:<18} "
                f"{format_number(value, 3)}"
            )

        classification_rows.append(row)

    # =========================================================================
    # LOW_POWDER ANALYSIS
    # =========================================================================

    print_section(
        "LOW_POWDER FEATURE ANALYSIS BY DURATION"
    )

    low_powder_df = events_df[
        events_df["Classification"]
        == "LOW_POWDER"
    ].copy()

    if low_powder_df.empty:

        print(
            "No LOW_POWDER events found."
        )

    else:

        print(
            f"LOW_POWDER events: "
            f"{len(low_powder_df)}"
        )

        print()

        for category in DURATION_ORDER:

            subset = low_powder_df[
                low_powder_df["Duration_Category"]
                == category
            ]

            if subset.empty:
                continue

            print(
                f"{category:<16} "
                f"{len(subset):4d} events"
            )

            print(
                f"  Duration:      "
                f"{subset['Duration_Frames'].mean():.2f} frames"
            )

            print(
                f"  Band 3:        "
                f"{subset['Mean_Band3'].mean():.1f}"
            )

            print(
                f"  Band 4:        "
                f"{subset['Mean_Band4'].mean():.1f}"
            )

            print(
                f"  Band 5:        "
                f"{subset['Mean_Band5'].mean():.1f}"
            )

            print(
                f"  Area:          "
                f"{subset['Mean_Area_mm2'].mean():.3f} mm²"
            )

            print(
                f"  Circularity:   "
                f"{subset['Mean_Circularity'].mean():.3f}"
            )

            print(
                f"  Aspect ratio:  "
                f"{subset['Mean_Aspect_Ratio'].mean():.3f}"
            )

            print()

    # =========================================================================
    # SHORT VS LONG LOW_POWDER EVENTS
    # =========================================================================

    print_section(
        "LOW_POWDER — SHORT VS LONG EVENTS"
    )

    comparison_rows = []

    if low_powder_df.empty:

        print(
            "No LOW_POWDER events found."
        )

    else:

        short_events = low_powder_df[
            low_powder_df["Duration_Frames"]
            <= 5
        ]

        long_events = low_powder_df[
            low_powder_df["Duration_Frames"]
            >= 10
        ]

        print(
            f"Short events (<=5 frames): "
            f"{len(short_events)}"
        )

        print(
            f"Long events (>=10 frames): "
            f"{len(long_events)}"
        )

        print()

        for label, subset in [
            ("SHORT_<=5", short_events),
            ("LONG_>=10", long_events),
        ]:

            if subset.empty:
                continue

            print(label)

            print(
                f"  Average duration: "
                f"{subset['Duration_Frames'].mean():.2f} frames"
            )

            print(
                f"  Band 3:           "
                f"{subset['Mean_Band3'].mean():.1f}"
            )

            print(
                f"  Band 4:           "
                f"{subset['Mean_Band4'].mean():.1f}"
            )

            print(
                f"  Band 5:           "
                f"{subset['Mean_Band5'].mean():.1f}"
            )

            print(
                f"  Area:             "
                f"{subset['Mean_Area_mm2'].mean():.3f} mm²"
            )

            print(
                f"  Circularity:      "
                f"{subset['Mean_Circularity'].mean():.3f}"
            )

            print(
                f"  Aspect ratio:     "
                f"{subset['Mean_Aspect_Ratio'].mean():.3f}"
            )

            print()

            row = {
                "Group": label,
                "Events": len(subset),
                "Mean_Duration_Frames": (
                    subset["Duration_Frames"].mean()
                ),
            }

            for column in FEATURE_COLUMNS:

                row[column] = subset[column].mean()

            comparison_rows.append(row)

    # =========================================================================
    # LONGEST LOW_POWDER EVENTS
    # =========================================================================

    print_section(
        "LONGEST LOW_POWDER EVENTS"
    )

    if low_powder_df.empty:

        print("None")

    else:

        longest = (
            low_powder_df
            .sort_values(
                "Duration_Frames",
                ascending=False,
            )
            .head(15)
        )

        for _, row in longest.iterrows():

            print(
                f"Event {int(row['Event_ID']):3d} | "
                f"L{int(row['Layer']):02d} | "
                f"{int(row['Duration_Frames']):4d} frames | "
                f"{row['Duration_Seconds']:.3f} s | "
                f"B3 {row['Mean_Band3']:.0f} | "
                f"B4 {row['Mean_Band4']:.0f} | "
                f"B5 {row['Mean_Band5']:.0f} | "
                f"area {row['Mean_Area_mm2']:.3f} | "
                f"cir {row['Mean_Circularity']:.3f} | "
                f"AR {row['Mean_Aspect_Ratio']:.3f}"
            )

    # =========================================================================
    # CORRELATION ANALYSIS
    # =========================================================================

    print_section(
        "DURATION VS FEATURE CORRELATIONS"
    )

    correlation_rows = []

    for classification in CLASSIFICATION_ORDER:

        subset = events_df[
            events_df["Classification"]
            == classification
        ]

        if len(subset) < 3:
            continue

        print()
        print(classification)

        for column in FEATURE_COLUMNS:

            valid = subset[
                [
                    "Duration_Frames",
                    column,
                ]
            ].dropna()

            if len(valid) < 3:
                continue

            # If the feature or duration has no variation, Pearson
            # correlation is undefined.
            if (
                valid["Duration_Frames"].nunique()
                < 2
                or valid[column].nunique()
                < 2
            ):

                print(
                    f"  {DISPLAY_NAMES[column]:<18} "
                    f"r = N/A (no variation)"
                )

                correlation_rows.append(
                    {
                        "Classification": classification,
                        "Feature": column,
                        "Correlation": None,
                    }
                )

                continue

            correlation = (
                valid[
                    "Duration_Frames"
                ]
                .corr(
                    valid[column]
                )
            )

            correlation_rows.append(
                {
                    "Classification": classification,
                    "Feature": column,
                    "Correlation": correlation,
                }
            )

            print(
                f"  {DISPLAY_NAMES[column]:<18} "
                f"r = {correlation:+.3f}"
            )

    # =========================================================================
    # LOW_POWDER CORRELATIONS
    # =========================================================================

    print_section(
        "LOW_POWDER DURATION VS FEATURE CORRELATIONS"
    )

    low_powder_correlation_rows = []

    if low_powder_df.empty:

        print(
            "No LOW_POWDER events found."
        )

    else:

        for column in FEATURE_COLUMNS:

            valid = low_powder_df[
                [
                    "Duration_Frames",
                    column,
                ]
            ].dropna()

            if len(valid) < 3:
                continue

            if (
                valid["Duration_Frames"].nunique()
                < 2
                or valid[column].nunique()
                < 2
            ):

                print(
                    f"{DISPLAY_NAMES[column]:<18} "
                    f"r = N/A (no variation)"
                )

                low_powder_correlation_rows.append(
                    {
                        "Feature": column,
                        "Correlation": None,
                    }
                )

                continue

            correlation = (
                valid[
                    "Duration_Frames"
                ]
                .corr(
                    valid[column]
                )
            )

            low_powder_correlation_rows.append(
                {
                    "Feature": column,
                    "Correlation": correlation,
                }
            )

            print(
                f"{DISPLAY_NAMES[column]:<18} "
                f"r = {correlation:+.3f}"
            )

    # =========================================================================
    # BUILD DATAFRAMES
    # =========================================================================

    summary_df = pd.DataFrame(
        summary_rows
    )

    classification_summary_df = pd.DataFrame(
        classification_rows
    )

    comparison_df = pd.DataFrame(
        comparison_rows
    )

    correlation_df = pd.DataFrame(
        correlation_rows
    )

    low_powder_correlation_df = pd.DataFrame(
        low_powder_correlation_rows
    )

    # =========================================================================
    # SAVE CSV OUTPUTS
    # =========================================================================

    summary_df.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    classification_summary_df.to_csv(
        DATASET
        / "transient_event_classification_features.csv",
        index=False,
    )

    comparison_df.to_csv(
        DATASET
        / "transient_event_short_vs_long.csv",
        index=False,
    )

    correlation_df.to_csv(
        DATASET
        / "transient_event_correlations.csv",
        index=False,
    )

    low_powder_correlation_df.to_csv(
        DATASET
        / "low_powder_duration_correlations.csv",
        index=False,
    )

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================

    print_header(
        "FEATURE ANALYSIS COMPLETE"
    )

    print()
    print(
        f"Duration summary:"
    )

    print(
        f"  {OUTPUT_CSV}"
    )

    print()
    print(
        "Additional outputs:"
    )

    print(
        f"  {DATASET / 'transient_event_classification_features.csv'}"
    )

    print(
        f"  {DATASET / 'transient_event_short_vs_long.csv'}"
    )

    print(
        f"  {DATASET / 'transient_event_correlations.csv'}"
    )

    print(
        f"  {DATASET / 'low_powder_duration_correlations.csv'}"
    )

    print()

    print(
        "No classifier thresholds or transient-event logic were changed."
    )

    print(
        "No persistence filtering was applied."
    )

    print()

    print("=" * 90)


if __name__ == "__main__":
    main()