"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Transient Event Context Analysis
===============================================================================

Examines the frames immediately before, during, and after transient events.

The purpose is to determine whether short classification events represent:

    1. Genuine transient changes in melt-pool behavior, or
    2. Brief threshold crossings / classification flicker.

For each LOW_POWDER event, the script examines:

    - Classification
    - Band 3
    - Band 4
    - Band 5
    - Area
    - Circularity
    - Aspect ratio

This analysis does NOT modify:
    - the classifier
    - transient-event detection
    - persistence filtering
    - existing MPAP outputs

Outputs:
    transient_event_context.csv
    transient_event_context_summary.csv
    transient_event_context_by_duration.csv
    transient_event_context_feature_changes.csv
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

DIAGNOSTIC_CSV = (
    DATASET / "classification_diagnostic.csv"
)

EVENTS_CSV = (
    DATASET / "transient_events.csv"
)

OUTPUT_CONTEXT_CSV = (
    DATASET / "transient_event_context.csv"
)

OUTPUT_SUMMARY_CSV = (
    DATASET / "transient_event_context_summary.csv"
)

OUTPUT_DURATION_CSV = (
    DATASET / "transient_event_context_by_duration.csv"
)

OUTPUT_FEATURE_CHANGE_CSV = (
    DATASET / "transient_event_context_feature_changes.csv"
)

CONTEXT_FRAMES = 5

TARGET_CLASSIFICATION = "LOW_POWDER"

DURATION_CATEGORIES = [
    "1_FRAME",
    "2_FRAMES",
    "3_5_FRAMES",
    "6_10_FRAMES",
    "11_30_FRAMES",
    "31_60_FRAMES",
    "61_PLUS_FRAMES",
]


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


def get_duration_category(duration):

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


def classify_context_position(
    frame_number,
    start_frame,
    end_frame,
):

    if frame_number < start_frame:
        return "BEFORE"

    if frame_number > end_frame:
        return "AFTER"

    return "EVENT"


def safe_mean(series):

    if series.empty:
        return None

    return float(series.mean())


def summarize_transition(context_df):

    if context_df.empty:
        return "NO_DATA"

    before = context_df[
        context_df["Context_Position"]
        == "BEFORE"
    ]

    event_frames = context_df[
        context_df["Context_Position"]
        == "EVENT"
    ]

    after = context_df[
        context_df["Context_Position"]
        == "AFTER"
    ]

    if (
        before.empty
        or event_frames.empty
        or after.empty
    ):
        return "INCOMPLETE_CONTEXT"

    before_classification = (
        before["Classification"]
        .mode()
        .iloc[0]
    )

    event_classification = (
        event_frames["Classification"]
        .mode()
        .iloc[0]
    )

    after_classification = (
        after["Classification"]
        .mode()
        .iloc[0]
    )

    if (
        before_classification != TARGET_CLASSIFICATION
        and event_classification == TARGET_CLASSIFICATION
        and after_classification != TARGET_CLASSIFICATION
    ):
        return "ISOLATED_TARGET"

    if (
        before_classification != TARGET_CLASSIFICATION
        and event_classification == TARGET_CLASSIFICATION
        and after_classification == TARGET_CLASSIFICATION
    ):
        return "TARGET_BEGINS"

    if (
        before_classification == TARGET_CLASSIFICATION
        and event_classification == TARGET_CLASSIFICATION
        and after_classification != TARGET_CLASSIFICATION
    ):
        return "TARGET_ENDS"

    if (
        before_classification == TARGET_CLASSIFICATION
        and event_classification == TARGET_CLASSIFICATION
        and after_classification == TARGET_CLASSIFICATION
    ):
        return "SUSTAINED_TARGET"

    if (
        before_classification == TARGET_CLASSIFICATION
        and event_classification != TARGET_CLASSIFICATION
        and after_classification == TARGET_CLASSIFICATION
    ):
        return "TARGET_INTERRUPTED"

    return "MIXED_CONTEXT"


def calculate_feature_change(
    context_df,
    feature,
):

    before = context_df[
        context_df["Context_Position"]
        == "BEFORE"
    ][feature].dropna()

    event_frames = context_df[
        context_df["Context_Position"]
        == "EVENT"
    ][feature].dropna()

    after = context_df[
        context_df["Context_Position"]
        == "AFTER"
    ][feature].dropna()

    before_mean = safe_mean(before)
    event_mean = safe_mean(event_frames)
    after_mean = safe_mean(after)

    if (
        before_mean is None
        or event_mean is None
        or after_mean is None
    ):
        return (
            before_mean,
            event_mean,
            after_mean,
            None,
            None,
        )

    if before_mean != 0:

        event_change_percent = (
            (
                event_mean
                - before_mean
            )
            / abs(before_mean)
            * 100.0
        )

    else:

        event_change_percent = None

    if event_mean != before_mean:

        recovery_percent = (
            (
                after_mean
                - event_mean
            )
            / (
                before_mean
                - event_mean
            )
            * 100.0
        )

    else:

        recovery_percent = None

    return (
        before_mean,
        event_mean,
        after_mean,
        event_change_percent,
        recovery_percent,
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print_header(
        "MPAP — TRANSIENT EVENT CONTEXT ANALYSIS"
    )

    print()
    print(f"Dataset:       {DATASET}")
    print(f"Diagnostic:    {DIAGNOSTIC_CSV}")
    print(f"Events:        {EVENTS_CSV}")
    print(
        f"Context:       ±{CONTEXT_FRAMES} frames"
    )
    print()

    # =========================================================================
    # CHECK INPUTS
    # =========================================================================

    if not DIAGNOSTIC_CSV.exists():

        print(
            f"ERROR: Could not find {DIAGNOSTIC_CSV}"
        )

        raise SystemExit(1)

    if not EVENTS_CSV.exists():

        print(
            f"ERROR: Could not find {EVENTS_CSV}"
        )

        raise SystemExit(1)

    # =========================================================================
    # LOAD DATA
    # =========================================================================

    diagnostic_df = pd.read_csv(
        DIAGNOSTIC_CSV
    )

    events_df = pd.read_csv(
        EVENTS_CSV
    )

    print(
        f"Diagnostic frames loaded: "
        f"{len(diagnostic_df)}"
    )

    print(
        f"Events loaded:            "
        f"{len(events_df)}"
    )

    # =========================================================================
    # CHECK COLUMNS
    # =========================================================================

    required_diagnostic_columns = [
        "Frame",
        "Classification",
        "Area_mm2",
        "Circularity",
        "Aspect_Ratio",
        "Band3",
        "Band4",
        "Band5",
    ]

    missing_diagnostic = [
        column
        for column in required_diagnostic_columns
        if column not in diagnostic_df.columns
    ]

    if missing_diagnostic:

        print()
        print(
            "ERROR: Missing diagnostic columns:"
        )

        for column in missing_diagnostic:
            print(
                f"  - {column}"
            )

        raise SystemExit(1)

    required_event_columns = [
        "Event_ID",
        "Layer",
        "Classification",
        "Start_Frame",
        "End_Frame",
        "Duration_Frames",
        "Duration_Seconds",
    ]

    missing_events = [
        column
        for column in required_event_columns
        if column not in events_df.columns
    ]

    if missing_events:

        print()
        print(
            "ERROR: Missing event columns:"
        )

        for column in missing_events:
            print(
                f"  - {column}"
            )

        raise SystemExit(1)

    # =========================================================================
    # NORMALIZE FRAME NUMBERS
    # =========================================================================

    diagnostic_df["Frame"] = pd.to_numeric(
        diagnostic_df["Frame"],
        errors="coerce",
    )

    events_df["Start_Frame"] = pd.to_numeric(
        events_df["Start_Frame"],
        errors="coerce",
    )

    events_df["End_Frame"] = pd.to_numeric(
        events_df["End_Frame"],
        errors="coerce",
    )

    events_df["Duration_Frames"] = pd.to_numeric(
        events_df["Duration_Frames"],
        errors="coerce",
    )

    diagnostic_df = diagnostic_df.dropna(
        subset=["Frame"]
    ).copy()

    events_df = events_df.dropna(
        subset=[
            "Start_Frame",
            "End_Frame",
            "Duration_Frames",
        ]
    ).copy()

    diagnostic_df["Frame"] = (
        diagnostic_df["Frame"]
        .astype(int)
    )

    events_df["Start_Frame"] = (
        events_df["Start_Frame"]
        .astype(int)
    )

    events_df["End_Frame"] = (
        events_df["End_Frame"]
        .astype(int)
    )

    events_df["Duration_Frames"] = (
        events_df["Duration_Frames"]
        .astype(int)
    )

    # =========================================================================
    # FILTER LOW_POWDER EVENTS
    # =========================================================================

    target_events = events_df[
        events_df["Classification"]
        == TARGET_CLASSIFICATION
    ].copy()

    target_events["Duration_Category"] = (
        target_events["Duration_Frames"]
        .apply(get_duration_category)
    )

    print()
    print(
        f"{TARGET_CLASSIFICATION} events: "
        f"{len(target_events)}"
    )

    if target_events.empty:

        print()
        print(
            f"No {TARGET_CLASSIFICATION} events found."
        )

        return

    # =========================================================================
    # INDEX DIAGNOSTIC DATA
    # =========================================================================

    diagnostic_by_frame = (
        diagnostic_df
        .set_index("Frame")
        .sort_index()
    )

    # =========================================================================
    # BUILD FRAME CONTEXT
    # =========================================================================

    print_section(
        "BUILDING EVENT CONTEXT"
    )

    context_rows = []

    for _, event in target_events.iterrows():

        event_id = int(
            event["Event_ID"]
        )

        layer = int(
            event["Layer"]
        )

        start_frame = int(
            event["Start_Frame"]
        )

        end_frame = int(
            event["End_Frame"]
        )

        duration_frames = int(
            event["Duration_Frames"]
        )

        event_duration_category = (
            event["Duration_Category"]
        )

        context_start = (
            start_frame
            - CONTEXT_FRAMES
        )

        context_end = (
            end_frame
            + CONTEXT_FRAMES
        )

        for frame_number in range(
            context_start,
            context_end + 1,
        ):

            if frame_number not in diagnostic_by_frame.index:
                continue

            row = diagnostic_by_frame.loc[
                frame_number
            ]

            if isinstance(
                row,
                pd.DataFrame,
            ):
                row = row.iloc[0]

            context_position = (
                classify_context_position(
                    frame_number,
                    start_frame,
                    end_frame,
                )
            )

            context_offset = (
                frame_number
                - start_frame
            )

            context_rows.append(
                {
                    "Event_ID": event_id,
                    "Layer": layer,
                    "Event_Start_Frame": start_frame,
                    "Event_End_Frame": end_frame,
                    "Event_Duration_Frames": duration_frames,
                    "Duration_Category": (
                        event_duration_category
                    ),
                    "Frame": frame_number,
                    "Context_Offset": context_offset,
                    "Context_Position": context_position,
                    "Classification": row[
                        "Classification"
                    ],
                    "Area_mm2": row[
                        "Area_mm2"
                    ],
                    "Circularity": row[
                        "Circularity"
                    ],
                    "Aspect_Ratio": row[
                        "Aspect_Ratio"
                    ],
                    "Band3": row[
                        "Band3"
                    ],
                    "Band4": row[
                        "Band4"
                    ],
                    "Band5": row[
                        "Band5"
                    ],
                }
            )

    context_df = pd.DataFrame(
        context_rows
    )

    print(
        f"Context frame records created: "
        f"{len(context_df)}"
    )

    if context_df.empty:

        print()
        print(
            "ERROR: No context records were created."
        )

        raise SystemExit(1)

    # =========================================================================
    # EVENT-LEVEL SUMMARY
    # =========================================================================

    print_section(
        "EVENT CONTEXT SUMMARY"
    )

    feature_columns = [
        "Band3",
        "Band4",
        "Band5",
        "Area_mm2",
        "Circularity",
        "Aspect_Ratio",
    ]

    summary_rows = []

    for event_id, event_context in (
        context_df
        .groupby("Event_ID")
    ):

        event_context = (
            event_context
            .sort_values("Frame")
        )

        first_row = event_context.iloc[0]

        event_layer = int(
            first_row["Layer"]
        )

        event_start_frame = int(
            first_row["Event_Start_Frame"]
        )

        event_end_frame = int(
            first_row["Event_End_Frame"]
        )

        event_duration_frames = int(
            first_row[
                "Event_Duration_Frames"
            ]
        )

        event_duration_category = (
            first_row["Duration_Category"]
        )

        transition = summarize_transition(
            event_context
        )

        before = event_context[
            event_context["Context_Position"]
            == "BEFORE"
        ]

        event_frames = event_context[
            event_context["Context_Position"]
            == "EVENT"
        ]

        after = event_context[
            event_context["Context_Position"]
            == "AFTER"
        ]

        if not before.empty:

            before_classification = (
                before["Classification"]
                .mode()
                .iloc[0]
            )

        else:

            before_classification = None

        if not event_frames.empty:

            event_classification = (
                event_frames["Classification"]
                .mode()
                .iloc[0]
            )

        else:

            event_classification = None

        if not after.empty:

            after_classification = (
                after["Classification"]
                .mode()
                .iloc[0]
            )

        else:

            after_classification = None

        summary = {
            "Event_ID": int(event_id),
            "Layer": event_layer,
            "Start_Frame": event_start_frame,
            "End_Frame": event_end_frame,
            "Duration_Frames": event_duration_frames,
            "Duration_Seconds": (
                event_duration_frames
                / 60.0
            ),
            "Duration_Category": (
                event_duration_category
            ),
            "Context_Transition": transition,
            "Before_Classification": (
                before_classification
            ),
            "Event_Classification": (
                event_classification
            ),
            "After_Classification": (
                after_classification
            ),
        }

        for feature in feature_columns:

            (
                before_mean,
                event_mean,
                after_mean,
                event_change_percent,
                recovery_percent,
            ) = calculate_feature_change(
                event_context,
                feature,
            )

            summary[
                f"{feature}_Before"
            ] = before_mean

            summary[
                f"{feature}_Event"
            ] = event_mean

            summary[
                f"{feature}_After"
            ] = after_mean

            summary[
                f"{feature}_Event_Change_Percent"
            ] = event_change_percent

            summary[
                f"{feature}_Recovery_Percent"
            ] = recovery_percent

        summary_rows.append(
            summary
        )

    summary_df = pd.DataFrame(
        summary_rows
    )

    # =========================================================================
    # CONTEXT TRANSITION SUMMARY
    # =========================================================================

    print_section(
        "CONTEXT TRANSITION SUMMARY"
    )

    transition_counts = (
        summary_df[
            "Context_Transition"
        ]
        .value_counts()
    )

    for transition, count in (
        transition_counts.items()
    ):

        print(
            f"{transition:<24} "
            f"{int(count):4d} events"
        )

    # =========================================================================
    # DURATION CATEGORY SUMMARY
    # =========================================================================

    print_section(
        "LOW_POWDER CONTEXT BY EVENT DURATION"
    )

    duration_summary_rows = []

    for category in DURATION_CATEGORIES:

        subset = summary_df[
            summary_df["Duration_Category"]
            == category
        ]

        if subset.empty:
            continue

        print()
        print(category)

        print(
            f"  Events: "
            f"{len(subset)}"
        )

        transition_counts = (
            subset[
                "Context_Transition"
            ]
            .value_counts()
        )

        for transition, count in (
            transition_counts.items()
        ):

            print(
                f"  {transition:<22} "
                f"{int(count):4d}"
            )

        row = {
            "Duration_Category": category,
            "Events": len(subset),
        }

        transition_names = [
            "ISOLATED_TARGET",
            "TARGET_BEGINS",
            "TARGET_ENDS",
            "SUSTAINED_TARGET",
            "TARGET_INTERRUPTED",
            "MIXED_CONTEXT",
            "INCOMPLETE_CONTEXT",
        ]

        for transition in transition_names:

            row[
                transition
            ] = int(
                (
                    subset[
                        "Context_Transition"
                    ]
                    == transition
                )
                .sum()
            )

        duration_summary_rows.append(
            row
        )

    duration_summary_df = pd.DataFrame(
        duration_summary_rows
    )

    # =========================================================================
    # FEATURE CHANGE SUMMARY
    # =========================================================================

    print_section(
        "LOW_POWDER FEATURE CHANGE: BEFORE → EVENT → AFTER"
    )

    feature_change_rows = []

    for category in DURATION_CATEGORIES:

        subset = summary_df[
            summary_df["Duration_Category"]
            == category
        ]

        if subset.empty:
            continue

        print()
        print(category)

        row = {
            "Duration_Category": category,
            "Events": len(subset),
        }

        for feature in feature_columns:

            before_mean = (
                subset[
                    f"{feature}_Before"
                ]
                .mean()
            )

            event_mean = (
                subset[
                    f"{feature}_Event"
                ]
                .mean()
            )

            after_mean = (
                subset[
                    f"{feature}_After"
                ]
                .mean()
            )

            event_change = (
                subset[
                    f"{feature}_Event_Change_Percent"
                ]
                .mean()
            )

            recovery = (
                subset[
                    f"{feature}_Recovery_Percent"
                ]
                .mean()
            )

            row[
                f"{feature}_Before"
            ] = before_mean

            row[
                f"{feature}_Event"
            ] = event_mean

            row[
                f"{feature}_After"
            ] = after_mean

            row[
                f"{feature}_Event_Change_Percent"
            ] = event_change

            row[
                f"{feature}_Recovery_Percent"
            ] = recovery

            if (
                before_mean is not None
                and event_mean is not None
                and after_mean is not None
            ):

                print(
                    f"  {feature:<18} "
                    f"{before_mean:>10.3f} → "
                    f"{event_mean:>10.3f} → "
                    f"{after_mean:>10.3f} | "
                    f"change "
                    f"{event_change:+7.2f}%"
                )

        feature_change_rows.append(
            row
        )

    feature_change_df = pd.DataFrame(
        feature_change_rows
    )

    # =========================================================================
    # ISOLATED EVENTS
    # =========================================================================

    print_section(
        "ISOLATED LOW_POWDER EVENTS"
    )

    isolated = summary_df[
        summary_df["Context_Transition"]
        == "ISOLATED_TARGET"
    ]

    print(
        f"Isolated LOW_POWDER events: "
        f"{len(isolated)}"
    )

    if not isolated.empty:

        print()

        isolated_sorted = (
            isolated
            .sort_values(
                "Duration_Frames",
                ascending=False,
            )
            .head(25)
        )

        for _, row in (
            isolated_sorted.iterrows()
        ):

            print(
                f"Event "
                f"{int(row['Event_ID']):3d} | "
                f"L"
                f"{int(row['Layer']):02d} | "
                f"{int(row['Duration_Frames']):3d} "
                f"frames | "
                f"B4 "
                f"{row['Band4_Event']:.1f} | "
                f"area "
                f"{row['Area_mm2_Event']:.3f} | "
                f"cir "
                f"{row['Circularity_Event']:.3f}"
            )

    # =========================================================================
    # ONE-FRAME EVENTS
    # =========================================================================

    print_section(
        "ONE-FRAME LOW_POWDER EVENTS"
    )

    one_frame = summary_df[
        summary_df["Duration_Frames"]
        == 1
    ]

    print(
        f"One-frame LOW_POWDER events: "
        f"{len(one_frame)}"
    )

    if not one_frame.empty:

        one_frame_transitions = (
            one_frame[
                "Context_Transition"
            ]
            .value_counts()
        )

        for transition, count in (
            one_frame_transitions.items()
        ):

            print(
                f"  {transition:<24} "
                f"{int(count):4d}"
            )

    # =========================================================================
    # LONG EVENTS
    # =========================================================================

    print_section(
        "LONG LOW_POWDER EVENTS"
    )

    long_events = summary_df[
        summary_df["Duration_Frames"]
        >= 10
    ]

    print(
        f"LOW_POWDER events >=10 frames: "
        f"{len(long_events)}"
    )

    if not long_events.empty:

        long_transitions = (
            long_events[
                "Context_Transition"
            ]
            .value_counts()
        )

        for transition, count in (
            long_transitions.items()
        ):

            print(
                f"  {transition:<24} "
                f"{int(count):4d}"
            )

    # =========================================================================
    # SAVE OUTPUTS
    # =========================================================================

    context_df.to_csv(
        OUTPUT_CONTEXT_CSV,
        index=False,
    )

    summary_df.to_csv(
        OUTPUT_SUMMARY_CSV,
        index=False,
    )

    duration_summary_df.to_csv(
        OUTPUT_DURATION_CSV,
        index=False,
    )

    feature_change_df.to_csv(
        OUTPUT_FEATURE_CHANGE_CSV,
        index=False,
    )

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================

    print_header(
        "TRANSIENT EVENT CONTEXT ANALYSIS COMPLETE"
    )

    print()
    print(
        "Frame-level context:"
    )

    print(
        f"  {OUTPUT_CONTEXT_CSV}"
    )

    print()
    print(
        "Event-level context:"
    )

    print(
        f"  {OUTPUT_SUMMARY_CSV}"
    )

    print()
    print(
        "Duration summary:"
    )

    print(
        f"  {OUTPUT_DURATION_CSV}"
    )

    print()
    print(
        "Feature-change summary:"
    )

    print(
        f"  {OUTPUT_FEATURE_CHANGE_CSV}"
    )

    print()
    print(
        "No classifier thresholds were changed."
    )

    print(
        "No transient-event detection logic was changed."
    )

    print(
        "No persistence filtering was applied."
    )

    print()
    print("=" * 90)


if __name__ == "__main__":
    main()