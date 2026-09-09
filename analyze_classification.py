"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Layer Trend + Layer Classification Analysis
===============================================================================
"""

import sys
from pathlib import Path

import matplotlib

# Prevent macOS / Python 3.14 GUI backend crashes.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

MIN_DOMINANT_PERCENT = 70.0

OUTPUT_CSV = "layer_trend_analysis.csv"
OUTPUT_CLASSIFICATION_CSV = "layer_classification_analysis.csv"

OUTPUT_B3 = "layer_b3_trend.png"
OUTPUT_B4 = "layer_b4_trend.png"
OUTPUT_CIRC = "layer_circularity_trend.png"
OUTPUT_CLASS = "layer_classification_trend.png"


# ============================================================
# GET DATASET FOLDER
# ============================================================

if len(sys.argv) != 2:
    print()
    print("Usage:")
    print('python analyze_classification.py "/path/to/dataset"')
    print()
    sys.exit(1)


DATASET_FOLDER = Path(sys.argv[1])


if not DATASET_FOLDER.exists():
    print()
    print("ERROR: Dataset folder does not exist:")
    print(DATASET_FOLDER)
    print()
    sys.exit(1)


CSV_PATH = DATASET_FOLDER / "classification_diagnostic.csv"


if not CSV_PATH.exists():
    print()
    print("ERROR: classification_diagnostic.csv was not found:")
    print(CSV_PATH)
    print()
    print("Run the batch processor on this dataset first.")
    print()
    sys.exit(1)


# ============================================================
# OUTPUT PATHS
# ============================================================

OUTPUT_CSV_PATH = DATASET_FOLDER / OUTPUT_CSV
OUTPUT_CLASSIFICATION_CSV_PATH = (
    DATASET_FOLDER / OUTPUT_CLASSIFICATION_CSV
)

OUTPUT_B3_PATH = DATASET_FOLDER / OUTPUT_B3
OUTPUT_B4_PATH = DATASET_FOLDER / OUTPUT_B4
OUTPUT_CIRC_PATH = DATASET_FOLDER / OUTPUT_CIRC
OUTPUT_CLASS_PATH = DATASET_FOLDER / OUTPUT_CLASS


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(CSV_PATH)

if df.empty:
    print()
    print("=" * 72)
    print("MPAP LAYER TREND + LAYER CLASSIFICATION ANALYSIS")
    print("=" * 72)
    print()
    print("Dataset:")
    print(DATASET_FOLDER)
    print()
    print("Total frames: 0")
    print("Active frames: 0")
    print("Layers detected: 0")
    print()
    print("No frames were found in classification_diagnostic.csv.")
    print("Nothing to analyze.")
    print()
    print("=" * 72)
    print("ANALYSIS COMPLETE")
    print("=" * 72)
    sys.exit(0)


required_columns = [
    "Frame",
    "Classification",
    "Area_mm2",
    "Circularity",
    "Aspect_Ratio",
    "Band3",
    "Band4",
    "Band5",
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:
    print()
    print("ERROR: classification_diagnostic.csv is missing required columns:")
    for column in missing_columns:
        print(" -", column)
    print()
    sys.exit(1)


df = df.sort_values("Frame").reset_index(drop=True)


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 72)
print("MPAP LAYER TREND + LAYER CLASSIFICATION ANALYSIS")
print("=" * 72)

print()
print("Dataset:")
print(DATASET_FOLDER)

print()
print("Total frames:", len(df))

print()
print("Layer classification threshold:", f"{MIN_DOMINANT_PERCENT:.1f}%")


# ============================================================
# IDENTIFY CONTIGUOUS CLASSIFICATION RUNS
# ============================================================

runs = []

start_index = 0
current_class = df.loc[0, "Classification"]


for i in range(1, len(df)):

    next_class = df.loc[i, "Classification"]

    if next_class != current_class:

        runs.append(
            {
                "start_index": start_index,
                "end_index": i - 1,
                "classification": current_class,
            }
        )

        start_index = i
        current_class = next_class


runs.append(
    {
        "start_index": start_index,
        "end_index": len(df) - 1,
        "classification": current_class,
    }
)


# ============================================================
# IDENTIFY ACTIVE SECTIONS
# ============================================================

active_sections = []

current_section = []
layer_number = 0


for run in runs:

    if run["classification"] == "LASER_OFF":

        if current_section:

            layer_number += 1

            active_sections.append(
                {
                    "Layer": layer_number,
                    "Start_Index": current_section[0],
                    "End_Index": current_section[-1],
                }
            )

            current_section = []

    else:

        current_section.extend(
            range(
                run["start_index"],
                run["end_index"] + 1,
            )
        )


# ============================================================
# HANDLE ACTIVE SECTION AT END OF FILE
# ============================================================

if current_section:

    layer_number += 1

    active_sections.append(
        {
            "Layer": layer_number,
            "Start_Index": current_section[0],
            "End_Index": current_section[-1],
        }
    )


# ============================================================
# ZERO-ACTIVE-FRAME HANDLING
# ============================================================

if not active_sections:

    print()
    print("-" * 72)
    print("NO ACTIVE LASER FRAMES DETECTED")
    print("-" * 72)

    print()
    print("Active frames: 0")
    print("Layers detected: 0")

    print()
    print(
        "This dataset contains only LASER_OFF frames, "
        "so there are no layers to analyze."
    )

    print()
    print("No layer trend CSV or plots were generated.")

    print()
    print("=" * 72)
    print("LAYER TREND + CLASSIFICATION ANALYSIS COMPLETE")
    print("=" * 72)

    sys.exit(0)


# ============================================================
# CALCULATE LAYER METRICS
# ============================================================

layer_rows = []


for section in active_sections:

    layer = section["Layer"]

    layer_data = df.iloc[
        section["Start_Index"]:
        section["End_Index"] + 1
    ].copy()

    active_frames = len(layer_data)

    if active_frames == 0:
        continue


    # --------------------------------------------------------
    # CLASSIFICATION COUNTS
    # --------------------------------------------------------

    good_count = (
        layer_data["Classification"] == "GOOD"
    ).sum()

    low_power_count = (
        layer_data["Classification"] == "LOW_POWER"
    ).sum()

    low_powder_count = (
        layer_data["Classification"] == "LOW_POWDER"
    ).sum()

    high_power_count = (
        layer_data["Classification"] == "HIGH_POWER"
    ).sum()

    unknown_count = (
        layer_data["Classification"] == "UNKNOWN"
    ).sum()


    # --------------------------------------------------------
    # CLASSIFICATION PERCENTAGES
    # --------------------------------------------------------

    good_percent = (
        good_count / active_frames * 100
    )

    low_power_percent = (
        low_power_count / active_frames * 100
    )

    low_powder_percent = (
        low_powder_count / active_frames * 100
    )

    high_power_percent = (
        high_power_count / active_frames * 100
    )

    unknown_percent = (
        unknown_count / active_frames * 100
    )


    # --------------------------------------------------------
    # LAYER METRICS
    # --------------------------------------------------------

    layer_rows.append(
        {
            "Layer": layer,

            "Start_Frame": int(
                layer_data["Frame"].iloc[0]
            ),

            "End_Frame": int(
                layer_data["Frame"].iloc[-1]
            ),

            "Active_Frames": active_frames,

            "Mean_Area_mm2": (
                layer_data["Area_mm2"].mean()
            ),

            "Mean_Circularity": (
                layer_data["Circularity"].mean()
            ),

            "Mean_Aspect_Ratio": (
                layer_data["Aspect_Ratio"].mean()
            ),

            "Mean_Band3": (
                layer_data["Band3"].mean()
            ),

            "Mean_Band4": (
                layer_data["Band4"].mean()
            ),

            "Mean_Band5": (
                layer_data["Band5"].mean()
            ),

            "GOOD": int(good_count),

            "LOW_POWER": int(low_power_count),

            "LOW_POWDER": int(low_powder_count),

            "HIGH_POWER": int(high_power_count),

            "UNKNOWN": int(unknown_count),

            "GOOD_Percent": good_percent,

            "LOW_POWER_Percent": low_power_percent,

            "LOW_POWDER_Percent": low_powder_percent,

            "HIGH_POWER_Percent": high_power_percent,

            "UNKNOWN_Percent": unknown_percent,
        }
    )


# ============================================================
# CREATE LAYER DATAFRAME
# ============================================================

layer_df = pd.DataFrame(layer_rows)


# ============================================================
# SAFETY CHECK
# ============================================================

if layer_df.empty:

    print()
    print("-" * 72)
    print("NO VALID ACTIVE LAYERS DETECTED")
    print("-" * 72)

    print()
    print("No layer metrics could be calculated.")

    print()
    print("=" * 72)
    print("LAYER TREND + CLASSIFICATION ANALYSIS COMPLETE")
    print("=" * 72)

    sys.exit(0)


# ============================================================
# SAVE LAYER TREND CSV
# ============================================================

layer_df.to_csv(
    OUTPUT_CSV_PATH,
    index=False,
)


# ============================================================
# PRINT LAYER TREND DATA
# ============================================================

print()
print("-" * 72)
print("LAYER TREND DATA")
print("-" * 72)


print(
    layer_df[
        [
            "Layer",
            "Start_Frame",
            "End_Frame",
            "Active_Frames",
            "Mean_Area_mm2",
            "Mean_Circularity",
            "Mean_Band3",
            "Mean_Band4",
            "GOOD_Percent",
            "LOW_POWER_Percent",
            "LOW_POWDER_Percent",
        ]
    ].to_string(index=False)
)


# ============================================================
# DETERMINE DOMINANT CLASSIFICATION
# ============================================================

classification_columns = [
    "GOOD_Percent",
    "LOW_POWER_Percent",
    "LOW_POWDER_Percent",
    "HIGH_POWER_Percent",
    "UNKNOWN_Percent",
]


classification_names = {
    "GOOD_Percent": "GOOD",
    "LOW_POWER_Percent": "LOW_POWER",
    "LOW_POWDER_Percent": "LOW_POWDER",
    "HIGH_POWER_Percent": "HIGH_POWER",
    "UNKNOWN_Percent": "UNKNOWN",
}


dominant_classifications = []
confidence_percentages = []
layer_statuses = []


for _, row in layer_df.iterrows():

    dominant_column = max(
        classification_columns,
        key=lambda column: row[column],
    )

    dominant_classification = (
        classification_names[dominant_column]
    )

    confidence = float(row[dominant_column])

    if confidence >= MIN_DOMINANT_PERCENT:
        layer_status = dominant_classification
    else:
        layer_status = "TRANSITION"

    dominant_classifications.append(
        dominant_classification
    )

    confidence_percentages.append(
        confidence
    )

    layer_statuses.append(
        layer_status
    )


layer_df["Dominant_Classification"] = (
    dominant_classifications
)

layer_df["Confidence_Percent"] = (
    confidence_percentages
)

layer_df["Layer_Status"] = (
    layer_statuses
)


# ============================================================
# SAVE LAYER CLASSIFICATION CSV
# ============================================================

layer_df.to_csv(
    OUTPUT_CLASSIFICATION_CSV_PATH,
    index=False,
)


# ============================================================
# PRINT LAYER CLASSIFICATION
# ============================================================

print()
print("-" * 72)
print("LAYER-LEVEL CLASSIFICATION")
print("-" * 72)

print()
print(
    "Rule: dominant classification must be "
    f">= {MIN_DOMINANT_PERCENT:.1f}%"
)

print()

print(
    layer_df[
        [
            "Layer",
            "Active_Frames",
            "GOOD_Percent",
            "LOW_POWDER_Percent",
            "LOW_POWER_Percent",
            "HIGH_POWER_Percent",
            "UNKNOWN_Percent",
            "Dominant_Classification",
            "Confidence_Percent",
            "Layer_Status",
        ]
    ].to_string(index=False)
)


# ============================================================
# LAYER STATUS SUMMARY
# ============================================================

status_counts = {
    "GOOD": 0,
    "LOW_POWDER": 0,
    "LOW_POWER": 0,
    "HIGH_POWER": 0,
    "UNKNOWN": 0,
    "TRANSITION": 0,
}


for status in layer_df["Layer_Status"]:

    if status in status_counts:
        status_counts[status] += 1


print()
print("-" * 72)
print("LAYER STATUS SUMMARY")
print("-" * 72)

print(
    f"GOOD             {status_counts['GOOD']}"
)

print(
    f"LOW_POWDER       {status_counts['LOW_POWDER']}"
)

print(
    f"LOW_POWER        {status_counts['LOW_POWER']}"
)

print(
    f"HIGH_POWER       {status_counts['HIGH_POWER']}"
)

print(
    f"UNKNOWN          {status_counts['UNKNOWN']}"
)

print(
    f"TRANSITION       {status_counts['TRANSITION']}"
)


# ============================================================
# PLOT 1 — BAND 3
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    layer_df["Layer"],
    layer_df["Mean_Band3"],
    marker="o",
)

plt.axhline(
    6000,
    linestyle="--",
    label="B3 = 6000",
)

plt.xlabel("Layer")
plt.ylabel("Mean Band 3")
plt.title("Mean Band 3 by Layer")
plt.legend()
plt.grid(True, alpha=0.25)
plt.tight_layout()

plt.savefig(
    OUTPUT_B3_PATH,
    dpi=200,
)

plt.close()


# ============================================================
# PLOT 2 — BAND 4
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    layer_df["Layer"],
    layer_df["Mean_Band4"],
    marker="o",
)

plt.axhline(
    200,
    linestyle="--",
    label="B4 = 200",
)

plt.xlabel("Layer")
plt.ylabel("Mean Band 4")
plt.title("Mean Band 4 by Layer")
plt.legend()
plt.grid(True, alpha=0.25)
plt.tight_layout()

plt.savefig(
    OUTPUT_B4_PATH,
    dpi=200,
)

plt.close()


# ============================================================
# PLOT 3 — CIRCULARITY
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    layer_df["Layer"],
    layer_df["Mean_Circularity"],
    marker="o",
)

plt.axhline(
    0.62,
    linestyle="--",
    label="Circularity = 0.62",
)

plt.xlabel("Layer")
plt.ylabel("Mean Circularity")
plt.title("Mean Circularity by Layer")
plt.legend()
plt.grid(True, alpha=0.25)
plt.tight_layout()

plt.savefig(
    OUTPUT_CIRC_PATH,
    dpi=200,
)

plt.close()


# ============================================================
# PLOT 4 — CLASSIFICATION
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    layer_df["Layer"],
    layer_df["GOOD_Percent"],
    marker="o",
    label="GOOD",
)

plt.plot(
    layer_df["Layer"],
    layer_df["LOW_POWDER_Percent"],
    marker="o",
    label="LOW_POWDER",
)

plt.plot(
    layer_df["Layer"],
    layer_df["LOW_POWER_Percent"],
    marker="o",
    label="LOW_POWER",
)

plt.plot(
    layer_df["Layer"],
    layer_df["HIGH_POWER_Percent"],
    marker="o",
    label="HIGH_POWER",
)

plt.plot(
    layer_df["Layer"],
    layer_df["UNKNOWN_Percent"],
    marker="o",
    label="UNKNOWN",
)

plt.xlabel("Layer")
plt.ylabel("Frames (%)")
plt.title("Classification Distribution by Layer")
plt.legend()
plt.grid(True, alpha=0.25)
plt.tight_layout()

plt.savefig(
    OUTPUT_CLASS_PATH,
    dpi=200,
)

plt.close()


# ============================================================
# SUMMARY
# ============================================================

print()
print("-" * 72)
print("SUMMARY")
print("-" * 72)

print(
    "Layers detected:",
    len(layer_df),
)

print(
    "Total active frames:",
    int(layer_df["Active_Frames"].sum()),
)


# ============================================================
# OUTPUT FILES
# ============================================================

print()
print("-" * 72)
print("OUTPUT FILES")
print("-" * 72)

print(OUTPUT_CSV_PATH)
print(OUTPUT_CLASSIFICATION_CSV_PATH)
print(OUTPUT_B3_PATH)
print(OUTPUT_B4_PATH)
print(OUTPUT_CIRC_PATH)
print(OUTPUT_CLASS_PATH)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 72)
print("LAYER TREND + CLASSIFICATION ANALYSIS COMPLETE")
print("=" * 72)