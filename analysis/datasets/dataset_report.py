"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Dataset Report Generator

Reads:
    classification_diagnostic.csv
    layer_trend_analysis.csv
    layer_classification_analysis.csv

Produces:
    dataset_report.txt
    dataset_summary.csv
===============================================================================
"""

import sys
from pathlib import Path

import pandas as pd


# =============================================================================
# CONFIGURATION
# =============================================================================

MIN_LAYER_CONFIDENCE = 70.0

CLASSIFICATIONS = [
    "LASER_OFF",
    "LOW_POWER",
    "LOW_POWDER",
    "GOOD",
    "HIGH_POWER",
    "UNKNOWN",
]

DEFECT_CLASSIFICATIONS = [
    "LOW_POWER",
    "LOW_POWDER",
    "HIGH_POWER",
    "UNKNOWN",
]

ORDERED_CLASSIFICATIONS = [
    "GOOD",
    "LOW_POWDER",
    "LOW_POWER",
    "HIGH_POWER",
    "UNKNOWN",
    "LASER_OFF",
]


# =============================================================================
# HELPERS
# =============================================================================

def print_header(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_section(title):
    print()
    print("-" * 72)
    print(title)
    print("-" * 72)


def percentage(count, total):
    if total == 0:
        return 0.0

    return (count / total) * 100.0


def safe_mean(series):
    if series is None:
        return 0.0

    if len(series) == 0:
        return 0.0

    return float(series.mean())


def read_csv_or_empty(path):
    """Read a CSV, returning an empty DataFrame for an empty file."""
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def determine_layer_status(row):
    classifications = {
        "GOOD": float(row.get("GOOD_Percent", 0.0)),
        "LOW_POWDER": float(row.get("LOW_POWDER_Percent", 0.0)),
        "LOW_POWER": float(row.get("LOW_POWER_Percent", 0.0)),
        "HIGH_POWER": float(row.get("HIGH_POWER_Percent", 0.0)),
        "UNKNOWN": float(row.get("UNKNOWN_Percent", 0.0)),
    }

    dominant = max(
        classifications,
        key=classifications.get,
    )

    confidence = classifications[dominant]

    if confidence >= MIN_LAYER_CONFIDENCE:
        status = dominant
    else:
        status = "TRANSITION"

    return dominant, confidence, status


def classify_dataset(layer_df, diagnostic_df):
    """
    Determine the overall dataset classification.

    Priority:
        1. No active frames -> LASER_OFF
        2. Majority of layers GOOD -> GOOD
        3. Majority of layers HIGH_POWER -> HIGH_POWER
        4. Majority of layers LOW_POWDER -> LOW_POWDER
        5. Majority of layers LOW_POWER -> LOW_POWER
        6. Otherwise use active-frame distribution
        7. Otherwise UNKNOWN
    """

    if diagnostic_df.empty:
        return "NO_DATA"

    active_df = diagnostic_df[
        diagnostic_df["Classification"] != "LASER_OFF"
    ].copy()

    if active_df.empty:
        return "LASER_OFF"

    if layer_df.empty:
        counts = active_df["Classification"].value_counts()

        if counts.empty:
            return "UNKNOWN"

        return str(counts.index[0])

    status_counts = (
        layer_df["Layer_Status"]
        .value_counts()
        .to_dict()
    )

    layer_count = len(layer_df)

    if layer_count > 0:
        good_layers = status_counts.get("GOOD", 0)

        if good_layers / layer_count >= 0.50:
            return "GOOD"

        high_power_layers = status_counts.get(
            "HIGH_POWER",
            0,
        )

        if high_power_layers / layer_count >= 0.50:
            return "HIGH_POWER"

        low_powder_layers = status_counts.get(
            "LOW_POWDER",
            0,
        )

        if low_powder_layers / layer_count >= 0.50:
            return "LOW_POWDER"

        low_power_layers = status_counts.get(
            "LOW_POWER",
            0,
        )

        if low_power_layers / layer_count >= 0.50:
            return "LOW_POWER"

    active_counts = active_df[
        "Classification"
    ].value_counts()

    if not active_counts.empty:
        dominant = str(active_counts.index[0])

        if dominant in CLASSIFICATIONS:
            return dominant

    return "UNKNOWN"


def describe_trend(first_value, last_value):
    """
    Return UP, DOWN, STABLE, or UNKNOWN.

    A 5% relative change is used as the stability band.
    """

    if pd.isna(first_value) or pd.isna(last_value):
        return "UNKNOWN"

    if first_value == 0:
        if last_value == 0:
            return "STABLE"

        return "UP"

    relative_change = (
        (last_value - first_value)
        / abs(first_value)
    ) * 100.0

    if relative_change > 5.0:
        return "UP"

    if relative_change < -5.0:
        return "DOWN"

    return "STABLE"


def find_transitions(layer_df):
    transitions = []

    if len(layer_df) < 2:
        return transitions

    previous_status = None

    for _, row in layer_df.iterrows():
        current_status = row["Layer_Status"]
        layer = int(row["Layer"])

        if previous_status is not None:
            if current_status != previous_status:
                transitions.append(
                    {
                        "Layer": layer,
                        "From": previous_status,
                        "To": current_status,
                    }
                )

        previous_status = current_status

    return transitions


def find_first_defect_layer(layer_df):
    if layer_df.empty:
        return None

    for _, row in layer_df.iterrows():
        status = row["Layer_Status"]

        if status in DEFECT_CLASSIFICATIONS:
            return int(row["Layer"])

        if status == "TRANSITION":
            return int(row["Layer"])

    return None



# =============================================================================
# DATASET DIAGNOSIS
# =============================================================================

def determine_initial_condition(layer_df, diagnostic_df):
    """Return the first meaningful condition observed in the dataset."""
    if not diagnostic_df.empty:
        active_df = diagnostic_df[
            diagnostic_df["Classification"] != "LASER_OFF"
        ]

        if active_df.empty:
            return "LASER_OFF"

    if layer_df.empty:
        return "UNKNOWN"

    return str(layer_df.iloc[0]["Layer_Status"])


def determine_final_condition(layer_df, diagnostic_df):
    """Return the final meaningful condition observed in the dataset."""
    if not diagnostic_df.empty:
        active_df = diagnostic_df[
            diagnostic_df["Classification"] != "LASER_OFF"
        ]

        if active_df.empty:
            return "LASER_OFF"

    if layer_df.empty:
        return "UNKNOWN"

    return str(layer_df.iloc[-1]["Layer_Status"])


def determine_process_behavior(layer_df):
    """Describe whether layer classification behavior is stable or evolving."""
    if layer_df.empty:
        return "NO_ACTIVE_PROCESS"

    statuses = [
        str(status)
        for status in layer_df["Layer_Status"].tolist()
    ]

    unique_statuses = list(dict.fromkeys(statuses))

    if len(unique_statuses) <= 1:
        return "STABLE"

    return "EVOLVING"


def determine_process_direction(
    layer_df,
    area_trend,
    circularity_trend,
    band3_trend,
    band4_trend,
    band5_trend,
):
    """Determine overall process direction from classification progression."""
    if layer_df.empty:
        return "UNKNOWN"

    statuses = [str(status) for status in layer_df["Layer_Status"].tolist()]

    if not statuses:
        return "UNKNOWN"

    first_status = statuses[0]
    last_status = statuses[-1]

    # If the classification remains unchanged, the process is stable.
    if first_status == last_status and len(set(statuses)) == 1:
        return "STABLE"

    defect_statuses = set(DEFECT_CLASSIFICATIONS)

    if first_status == "GOOD" and last_status in defect_statuses:
        return "DETERIORATING"

    if first_status in defect_statuses and last_status == "GOOD":
        return "IMPROVING"

    first_index = (
        ORDERED_CLASSIFICATIONS.index(first_status)
        if first_status in ORDERED_CLASSIFICATIONS
        else None
    )
    last_index = (
        ORDERED_CLASSIFICATIONS.index(last_status)
        if last_status in ORDERED_CLASSIFICATIONS
        else None
    )

    if first_index is not None and last_index is not None:
        if last_index > first_index:
            return "DETERIORATING"
        if last_index < first_index:
            return "IMPROVING"

    worsening_signals = 0
    improving_signals = 0

    if circularity_trend == "DOWN":
        worsening_signals += 1
    elif circularity_trend == "UP":
        improving_signals += 1

    if band4_trend == "DOWN":
        worsening_signals += 1
    elif band4_trend == "UP":
        improving_signals += 1

    if band5_trend == "UP":
        worsening_signals += 1
    elif band5_trend == "DOWN":
        improving_signals += 1

    if area_trend == "DOWN":
        worsening_signals += 1
    elif area_trend == "UP":
        improving_signals += 1

    if band3_trend == "DOWN":
        worsening_signals += 1
    elif band3_trend == "UP":
        improving_signals += 1

    if worsening_signals > improving_signals:
        return "DETERIORATING"

    if improving_signals > worsening_signals:
        return "IMPROVING"

    if len(set(statuses)) > 1:
        return "MIXED"

    return "STABLE"

def determine_dominant_defect(layer_df):
    """Return the most common confirmed defect layer classification."""
    if layer_df.empty:
        return "NONE"

    defect_df = layer_df[
        layer_df["Layer_Status"].isin(DEFECT_CLASSIFICATIONS)
    ]

    if defect_df.empty:
        return "NONE"

    counts = defect_df["Layer_Status"].value_counts()

    return str(counts.index[0])


def find_first_abnormal_layer(layer_df):
    """Return the first layer that is not classified as GOOD."""
    if layer_df.empty:
        return None

    for _, row in layer_df.iterrows():
        status = str(row["Layer_Status"])

        if status != "GOOD":
            return int(row["Layer"])

    return None


def find_first_confirmed_defect_layer(layer_df):
    """Return the first layer with a confirmed defect classification."""
    if layer_df.empty:
        return None

    for _, row in layer_df.iterrows():
        status = str(row["Layer_Status"])

        if status in DEFECT_CLASSIFICATIONS:
            return int(row["Layer"])

    return None


def generate_diagnosis_text(
    initial_condition,
    final_condition,
    process_behavior,
    process_direction,
    dominant_defect,
    first_abnormal_layer,
    first_confirmed_defect_layer,
    transitions,
    area_trend,
    circularity_trend,
    band3_trend,
    band4_trend,
    band5_trend,
):
    """Generate a concise plain-English dataset diagnosis."""
    if process_behavior == "NO_ACTIVE_PROCESS":
        return (
            "No active laser process was detected, so a process "
            "evolution diagnosis could not be established."
        )

    parts = [
        f"The build began in {initial_condition} condition and ended "
        f"in {final_condition} condition."
    ]

    if process_direction == "DETERIORATING":
        parts.append(
            "The observed process behavior indicates deterioration."
        )
    elif process_direction == "IMPROVING":
        parts.append(
            "The observed process behavior indicates improvement."
        )
    elif process_direction == "STABLE":
        parts.append(
            "The observed process behavior remained stable."
        )
    else:
        parts.append(
            "The observed process behavior was mixed."
        )

    if dominant_defect != "NONE":
        parts.append(
            f"The most common confirmed defect classification was "
            f"{dominant_defect}."
        )
    else:
        parts.append(
            "No confirmed defect classification dominated the build."
        )

    if first_abnormal_layer is not None:
        parts.append(
            f"The first abnormal layer was Layer {first_abnormal_layer}."
        )

    if first_confirmed_defect_layer is not None:
        parts.append(
            f"The first confirmed defect occurred at "
            f"Layer {first_confirmed_defect_layer}."
        )

    parts.append(
        f"{len(transitions)} layer-level classification changes "
        f"were observed."
    )

    parts.append(
        "Observed metric trends: "
        f"area {area_trend.lower()}, "
        f"circularity {circularity_trend.lower()}, "
        f"Band 3 {band3_trend.lower()}, "
        f"Band 4 {band4_trend.lower()}, "
        f"Band 5 {band5_trend.lower()}."
    )

    return " ".join(parts)


# =============================================================================
# ARGUMENTS
# =============================================================================

if len(sys.argv) != 2:
    print()
    print("Usage:")
    print(
        'python dataset_report.py "/path/to/dataset"'
    )
    print()
    sys.exit(1)


DATASET_FOLDER = Path(sys.argv[1])


if not DATASET_FOLDER.exists():
    print()
    print("ERROR: Dataset folder does not exist:")
    print(DATASET_FOLDER)
    print()
    sys.exit(1)


DIAGNOSTIC_CSV = (
    DATASET_FOLDER /
    "classification_diagnostic.csv"
)

LAYER_TREND_CSV = (
    DATASET_FOLDER /
    "layer_trend_analysis.csv"
)

LAYER_CLASSIFICATION_CSV = (
    DATASET_FOLDER /
    "layer_classification_analysis.csv"
)

REPORT_TXT = (
    DATASET_FOLDER /
    "dataset_report.txt"
)

SUMMARY_CSV = (
    DATASET_FOLDER /
    "dataset_summary.csv"
)


# =============================================================================
# CHECK INPUTS
# =============================================================================

if not DIAGNOSTIC_CSV.exists():
    print()
    print("ERROR: classification_diagnostic.csv was not found:")
    print(DIAGNOSTIC_CSV)
    print()
    print(
        "Run the batch processor on this dataset first."
    )
    print()
    sys.exit(1)


# =============================================================================
# LOAD DATA
# =============================================================================

diagnostic_df = pd.read_csv(
    DIAGNOSTIC_CSV
)

diagnostic_df = diagnostic_df.sort_values(
    "Frame"
).reset_index(drop=True)


layer_df = read_csv_or_empty(
    LAYER_TREND_CSV
)


layer_classification_df = read_csv_or_empty(
    LAYER_CLASSIFICATION_CSV
)


# =============================================================================
# RECONSTRUCT LAYER CLASSIFICATION IF NECESSARY
# =============================================================================

if not layer_df.empty:

    if (
        "Layer_Status" not in layer_df.columns
        or "Dominant_Classification"
        not in layer_df.columns
        or "Confidence_Percent"
        not in layer_df.columns
    ):

        layer_statuses = []

        for _, row in layer_df.iterrows():

            dominant, confidence, status = (
                determine_layer_status(row)
            )

            layer_statuses.append(
                (
                    dominant,
                    confidence,
                    status,
                )
            )

        layer_df[
            "Dominant_Classification"
        ] = [
            item[0]
            for item in layer_statuses
        ]

        layer_df[
            "Confidence_Percent"
        ] = [
            item[1]
            for item in layer_statuses
        ]

        layer_df[
            "Layer_Status"
        ] = [
            item[2]
            for item in layer_statuses
        ]


# =============================================================================
# BASIC DATASET METRICS
# =============================================================================

total_frames = len(diagnostic_df)

active_df = diagnostic_df[
    diagnostic_df["Classification"] != "LASER_OFF"
].copy()

active_frames = len(active_df)

laser_off_frames = (
    diagnostic_df["Classification"]
    == "LASER_OFF"
).sum()


frame_counts = (
    diagnostic_df["Classification"]
    .value_counts()
    .to_dict()
)


frame_percentages = {}

for classification in CLASSIFICATIONS:

    count = frame_counts.get(
        classification,
        0,
    )

    frame_percentages[classification] = (
        percentage(
            count,
            total_frames,
        )
    )


# =============================================================================
# OVERALL DATASET CLASSIFICATION
# =============================================================================

overall_classification = classify_dataset(
    layer_df,
    diagnostic_df,
)


# =============================================================================
# LAYER METRICS
# =============================================================================

layer_count = len(layer_df)

if layer_count > 0:

    active_layer_frames = int(
        layer_df["Active_Frames"].sum()
    )

    mean_area = safe_mean(
        layer_df["Mean_Area_mm2"]
    )

    mean_circularity = safe_mean(
        layer_df["Mean_Circularity"]
    )

    mean_band3 = safe_mean(
        layer_df["Mean_Band3"]
    )

    mean_band4 = safe_mean(
        layer_df["Mean_Band4"]
    )

    mean_band5 = safe_mean(
        layer_df["Mean_Band5"]
    )

    mean_layer_confidence = safe_mean(
        layer_df["Confidence_Percent"]
    )

else:

    active_layer_frames = 0

    mean_area = 0.0
    mean_circularity = 0.0
    mean_band3 = 0.0
    mean_band4 = 0.0
    mean_band5 = 0.0
    mean_layer_confidence = 0.0


# =============================================================================
# LAYER STATUS COUNTS
# =============================================================================

layer_status_counts = {}

for status in [
    "GOOD",
    "LOW_POWDER",
    "LOW_POWER",
    "HIGH_POWER",
    "UNKNOWN",
    "TRANSITION",
]:

    if layer_df.empty:
        count = 0
    else:
        count = int(
            (
                layer_df["Layer_Status"]
                == status
            ).sum()
        )

    layer_status_counts[status] = count


# =============================================================================
# FIRST AND LAST LAYER TRENDS
# =============================================================================

if layer_count > 0:

    first_layer = layer_df.iloc[0]
    last_layer = layer_df.iloc[-1]

    area_trend = describe_trend(
        first_layer["Mean_Area_mm2"],
        last_layer["Mean_Area_mm2"],
    )

    circularity_trend = describe_trend(
        first_layer["Mean_Circularity"],
        last_layer["Mean_Circularity"],
    )

    band3_trend = describe_trend(
        first_layer["Mean_Band3"],
        last_layer["Mean_Band3"],
    )

    band4_trend = describe_trend(
        first_layer["Mean_Band4"],
        last_layer["Mean_Band4"],
    )

    band5_trend = describe_trend(
        first_layer["Mean_Band5"],
        last_layer["Mean_Band5"],
    )

else:

    area_trend = "UNKNOWN"
    circularity_trend = "UNKNOWN"
    band3_trend = "UNKNOWN"
    band4_trend = "UNKNOWN"
    band5_trend = "UNKNOWN"


# =============================================================================
# TRANSITIONS
# =============================================================================

transitions = find_transitions(
    layer_df
)

first_defect_layer = find_first_defect_layer(
    layer_df
)

first_abnormal_layer = find_first_abnormal_layer(
    layer_df
)

first_confirmed_defect_layer = find_first_confirmed_defect_layer(
    layer_df
)

initial_condition = determine_initial_condition(
    layer_df,
    diagnostic_df,
)

final_condition = determine_final_condition(
    layer_df,
    diagnostic_df,
)

process_behavior = determine_process_behavior(
    layer_df,
)

process_direction = determine_process_direction(
    layer_df,
    area_trend,
    circularity_trend,
    band3_trend,
    band4_trend,
    band5_trend,
)

dominant_defect = determine_dominant_defect(
    layer_df,
)

diagnosis_text = generate_diagnosis_text(
    initial_condition,
    final_condition,
    process_behavior,
    process_direction,
    dominant_defect,
    first_abnormal_layer,
    first_confirmed_defect_layer,
    transitions,
    area_trend,
    circularity_trend,
    band3_trend,
    band4_trend,
    band5_trend,
)


# =============================================================================
# BUILD SUMMARY CSV
# =============================================================================

summary_rows = [
    {
        "Dataset": DATASET_FOLDER.name,
        "Overall_Classification": overall_classification,
        "Total_Frames": total_frames,
        "Active_Frames": active_frames,
        "Laser_Off_Frames": laser_off_frames,
        "Layers": layer_count,
        "Mean_Area_mm2": mean_area,
        "Mean_Circularity": mean_circularity,
        "Mean_Band3": mean_band3,
        "Mean_Band4": mean_band4,
        "Mean_Band5": mean_band5,
        "Mean_Layer_Confidence_Percent": (
            mean_layer_confidence
        ),
        "GOOD_Layers": layer_status_counts[
            "GOOD"
        ],
        "LOW_POWDER_Layers": layer_status_counts[
            "LOW_POWDER"
        ],
        "LOW_POWER_Layers": layer_status_counts[
            "LOW_POWER"
        ],
        "HIGH_POWER_Layers": layer_status_counts[
            "HIGH_POWER"
        ],
        "UNKNOWN_Layers": layer_status_counts[
            "UNKNOWN"
        ],
        "TRANSITION_Layers": layer_status_counts[
            "TRANSITION"
        ],
        "First_Defect_Layer": (
            first_defect_layer
            if first_defect_layer is not None
            else ""
        ),
        "Initial_Condition": initial_condition,
        "Final_Condition": final_condition,
        "Process_Behavior": process_behavior,
        "Process_Direction": process_direction,
        "First_Abnormal_Layer": (
            first_abnormal_layer
            if first_abnormal_layer is not None
            else ""
        ),
        "First_Confirmed_Defect_Layer": (
            first_confirmed_defect_layer
            if first_confirmed_defect_layer is not None
            else ""
        ),
        "Dominant_Defect": dominant_defect,
        "Classification_Transitions": len(transitions),
        "Area_Trend": area_trend,
        "Circularity_Trend": circularity_trend,
        "Band3_Trend": band3_trend,
        "Band4_Trend": band4_trend,
        "Band5_Trend": band5_trend,
    }
]


summary_df = pd.DataFrame(
    summary_rows
)

summary_df.to_csv(
    SUMMARY_CSV,
    index=False,
)


# =============================================================================
# BUILD TEXT REPORT
# =============================================================================

report_lines = []

report_lines.append(
    "=" * 72
)

report_lines.append(
    "MPAP DATASET REPORT"
)

report_lines.append(
    "=" * 72
)

report_lines.append("")

report_lines.append(
    f"Dataset: {DATASET_FOLDER.name}"
)

report_lines.append(
    f"Path: {DATASET_FOLDER}"
)

report_lines.append("")

report_lines.append(
    "OVERALL ASSESSMENT"
)

report_lines.append(
    "-" * 72
)

report_lines.append(
    f"Overall Classification: "
    f"{overall_classification}"
)

if overall_classification == "LASER_OFF":

    report_lines.append(
        "Assessment: No active laser frames were detected."
    )

elif overall_classification == "GOOD":

    report_lines.append(
        "Assessment: The majority of analyzed layers "
        "are classified as GOOD."
    )

elif overall_classification in DEFECT_CLASSIFICATIONS:

    report_lines.append(
        "Assessment: A defect-related classification "
        "dominates the dataset."
    )

else:

    report_lines.append(
        "Assessment: The dataset contains mixed or "
        "uncertain behavior."
    )


# =============================================================================
# DATASET DIAGNOSIS
# =============================================================================

report_lines.append("")

report_lines.append(
    "DATASET DIAGNOSIS"
)

report_lines.append(
    "-" * 72
)

report_lines.append(
    f"Initial condition:           {initial_condition}"
)

report_lines.append(
    f"Final condition:             {final_condition}"
)

report_lines.append(
    f"Process behavior:            {process_behavior}"
)

report_lines.append(
    f"Process direction:           {process_direction}"
)

if first_abnormal_layer is None:

    report_lines.append(
        "First abnormal layer:        None"
    )

else:

    report_lines.append(
        f"First abnormal layer:        {first_abnormal_layer}"
    )

if first_confirmed_defect_layer is None:

    report_lines.append(
        "First confirmed defect:      None"
    )

else:

    report_lines.append(
        f"First confirmed defect:      {first_confirmed_defect_layer}"
    )

report_lines.append(
    f"Dominant defect:             {dominant_defect}"
)

report_lines.append(
    f"Classification transitions:  {len(transitions)}"
)

report_lines.append("")

report_lines.append(
    "Diagnosis:"
)

report_lines.append(
    diagnosis_text
)


# =============================================================================
# DATASET SUMMARY
# =============================================================================

report_lines.append("")

report_lines.append(
    "DATASET SUMMARY"
)

report_lines.append(
    "-" * 72
)

report_lines.append(
    f"Total frames:       {total_frames}"
)

report_lines.append(
    f"Active frames:      {active_frames}"
)

report_lines.append(
    f"LASER_OFF frames:   {laser_off_frames}"
)

report_lines.append(
    f"Layers detected:    {layer_count}"
)


# =============================================================================
# FRAME CLASSIFICATION
# =============================================================================

report_lines.append("")

report_lines.append(
    "FRAME-LEVEL CLASSIFICATION"
)

report_lines.append(
    "-" * 72
)

for classification in ORDERED_CLASSIFICATIONS:

    count = frame_counts.get(
        classification,
        0,
    )

    pct = frame_percentages.get(
        classification,
        0.0,
    )

    report_lines.append(
        f"{classification:<18}"
        f"{count:>8}"
        f"  ({pct:>6.2f}%)"
    )


# =============================================================================
# LAYER CLASSIFICATION
# =============================================================================

report_lines.append("")

report_lines.append(
    "LAYER-LEVEL CLASSIFICATION"
)

report_lines.append(
    "-" * 72
)

report_lines.append(
    f"{'GOOD':<18}"
    f"{layer_status_counts['GOOD']:>8}"
)

report_lines.append(
    f"{'LOW_POWDER':<18}"
    f"{layer_status_counts['LOW_POWDER']:>8}"
)

report_lines.append(
    f"{'LOW_POWER':<18}"
    f"{layer_status_counts['LOW_POWER']:>8}"
)

report_lines.append(
    f"{'HIGH_POWER':<18}"
    f"{layer_status_counts['HIGH_POWER']:>8}"
)

report_lines.append(
    f"{'UNKNOWN':<18}"
    f"{layer_status_counts['UNKNOWN']:>8}"
)

report_lines.append(
    f"{'TRANSITION':<18}"
    f"{layer_status_counts['TRANSITION']:>8}"
)


# =============================================================================
# LAYER METRICS
# =============================================================================

report_lines.append("")

report_lines.append(
    "AVERAGE MELT POOL METRICS"
)

report_lines.append(
    "-" * 72
)

report_lines.append(
    f"Mean area:          {mean_area:.4f} mm²"
)

report_lines.append(
    f"Mean circularity:   {mean_circularity:.4f}"
)

report_lines.append(
    f"Mean Band 3:        {mean_band3:.2f}"
)

report_lines.append(
    f"Mean Band 4:        {mean_band4:.2f}"
)

report_lines.append(
    f"Mean Band 5:        {mean_band5:.2f}"
)

report_lines.append(
    f"Mean layer confidence: "
    f"{mean_layer_confidence:.2f}%"
)


# =============================================================================
# TRENDS
# =============================================================================

report_lines.append("")

report_lines.append(
    "LAYER TRENDS"
)

report_lines.append(
    "-" * 72
)

report_lines.append(
    f"Area:               {area_trend}"
)

report_lines.append(
    f"Circularity:        {circularity_trend}"
)

report_lines.append(
    f"Band 3:             {band3_trend}"
)

report_lines.append(
    f"Band 4:             {band4_trend}"
)

report_lines.append(
    f"Band 5:             {band5_trend}"
)


# =============================================================================
# FIRST DEFECT
# =============================================================================

report_lines.append("")

report_lines.append(
    "DEFECT DETECTION"
)

report_lines.append(
    "-" * 72
)

if first_defect_layer is None:

    report_lines.append(
        "First defect layer: None detected"
    )

else:

    report_lines.append(
        f"First defect/transition layer: "
        f"{first_defect_layer}"
    )


# =============================================================================
# TRANSITIONS
# =============================================================================

report_lines.append("")

report_lines.append(
    "CLASSIFICATION TRANSITIONS"
)

report_lines.append(
    "-" * 72
)

if not transitions:

    report_lines.append(
        "No layer-level classification transitions detected."
    )

else:

    for transition in transitions:

        report_lines.append(
            f"Layer {transition['Layer']:>3}: "
            f"{transition['From']} -> "
            f"{transition['To']}"
        )


# =============================================================================
# PER-LAYER DETAIL
# =============================================================================

report_lines.append("")

report_lines.append(
    "PER-LAYER SUMMARY"
)

report_lines.append(
    "-" * 72
)

if layer_df.empty:

    report_lines.append(
        "No layer data available."
    )

else:

    for _, row in layer_df.iterrows():

        layer = int(
            row["Layer"]
        )

        status = row[
            "Layer_Status"
        ]

        confidence = float(
            row["Confidence_Percent"]
        )

        area = float(
            row["Mean_Area_mm2"]
        )

        circularity = float(
            row["Mean_Circularity"]
        )

        band3 = float(
            row["Mean_Band3"]
        )

        band4 = float(
            row["Mean_Band4"]
        )

        report_lines.append(
            f"Layer {layer:>3} | "
            f"{status:<11} | "
            f"Confidence {confidence:>6.2f}% | "
            f"Area {area:>7.3f} mm² | "
            f"Circ {circularity:>6.3f} | "
            f"B3 {band3:>8.1f} | "
            f"B4 {band4:>8.1f}"
        )


# =============================================================================
# OUTPUT FILES
# =============================================================================

report_lines.append("")

report_lines.append(
    "OUTPUT FILES"
)

report_lines.append(
    "-" * 72
)

report_lines.append(
    str(REPORT_TXT)
)

report_lines.append(
    str(SUMMARY_CSV)
)

if LAYER_TREND_CSV.exists():

    report_lines.append(
        str(LAYER_TREND_CSV)
    )

if LAYER_CLASSIFICATION_CSV.exists():

    report_lines.append(
        str(LAYER_CLASSIFICATION_CSV)
    )


report_lines.append("")

report_lines.append(
    "=" * 72
)

report_lines.append(
    "MPAP DATASET REPORT COMPLETE"
)

report_lines.append(
    "=" * 72
)


# =============================================================================
# WRITE REPORT
# =============================================================================

report_text = "\n".join(
    report_lines
)

REPORT_TXT.write_text(
    report_text,
    encoding="utf-8",
)


# =============================================================================
# PRINT REPORT
# =============================================================================

print()

print(report_text)
