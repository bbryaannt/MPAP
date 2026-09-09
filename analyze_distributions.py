"""
===============================================================================
MPAP
Melt Pool Analysis Platform

2D Feature Distribution Analysis
===============================================================================
"""

import os

import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# DATASET PATHS
# =============================================================================

GOOD_CSV = (
    "/Volumes/Army Research Lab/dat Files/"
    "test_1_good_images/classification_diagnostic.csv"
)

BAD_CSV = (
    "/Volumes/Army Research Lab/dat Files/"
    "test_4_too_low_powder/classification_diagnostic.csv"
)


# =============================================================================
# CLASSIFIER THRESHOLDS
# =============================================================================

CIRCULARITY_THRESHOLD = 0.62
BAND4_THRESHOLD = 200


# =============================================================================
# LOAD DATA
# =============================================================================

def load_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found:\n{path}")

    df = pd.read_csv(path)

    if "Classification" in df.columns:
        df = df[df["Classification"] != "LASER_OFF"].copy()

    return df


# =============================================================================
# MAIN
# =============================================================================

def main():

    print()
    print("=" * 80)
    print("MPAP 2D FEATURE DISTRIBUTION ANALYSIS")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # Load data
    # -------------------------------------------------------------------------

    good = load_data(GOOD_CSV)
    bad = load_data(BAD_CSV)

    print()
    print(f"Known-good active frames:       {len(good)}")
    print(f"Too-low-powder active frames:   {len(bad)}")

    # -------------------------------------------------------------------------
    # Classification counts
    # -------------------------------------------------------------------------

    print()
    print("=" * 80)
    print("TOO-LOW-POWDER CLASSIFICATION COUNTS")
    print("=" * 80)

    print(
        bad["Classification"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    # -------------------------------------------------------------------------
    # Create output directory
    # -------------------------------------------------------------------------

    output_dir = os.path.dirname(BAD_CSV)

    # -------------------------------------------------------------------------
    # Circularity vs Band 4
    # -------------------------------------------------------------------------

    plt.figure(figsize=(11, 8))

    # Too-low-powder dataset
    for classification in [
        "LOW_POWER",
        "LOW_POWDER",
        "GOOD",
        "HIGH_POWER",
        "UNKNOWN",
    ]:

        subset = bad[
            bad["Classification"] == classification
        ]

        if len(subset) == 0:
            continue

        plt.scatter(
            subset["Circularity"],
            subset["Band4"],
            s=8,
            alpha=0.35,
            label=f"Bad: {classification}",
        )

    # Known-good dataset
    plt.scatter(
        good["Circularity"],
        good["Band4"],
        s=70,
        marker="x",
        linewidths=2,
        label="Known-good",
    )

    # Threshold lines
    plt.axvline(
        CIRCULARITY_THRESHOLD,
        linestyle="--",
        linewidth=2,
        label=f"Circularity threshold = {CIRCULARITY_THRESHOLD}",
    )

    plt.axhline(
        BAND4_THRESHOLD,
        linestyle="--",
        linewidth=2,
        label=f"Band 4 threshold = {BAND4_THRESHOLD}",
    )

    plt.xlabel("Circularity")
    plt.ylabel("Band 4 Pixel Count")
    plt.title("Circularity vs Band 4")
    plt.legend()
    plt.grid(alpha=0.25)

    plt.tight_layout()

    output_path = os.path.join(
        output_dir,
        "circularity_vs_band4.png",
    )

    plt.savefig(output_path, dpi=200)
    plt.close()

    print()
    print("Output:")
    print(output_path)

    # -------------------------------------------------------------------------
    # Circularity vs Band 4 — classified regions only
    # -------------------------------------------------------------------------

    plt.figure(figsize=(11, 8))

    low_power = bad[
        bad["Classification"] == "LOW_POWER"
    ]

    low_powder = bad[
        bad["Classification"] == "LOW_POWDER"
    ]

    good_bad = bad[
        bad["Classification"] == "GOOD"
    ]

    if len(low_power) > 0:
        plt.scatter(
            low_power["Circularity"],
            low_power["Band4"],
            s=8,
            alpha=0.35,
            label="LOW_POWER",
        )

    if len(low_powder) > 0:
        plt.scatter(
            low_powder["Circularity"],
            low_powder["Band4"],
            s=8,
            alpha=0.35,
            label="LOW_POWDER",
        )

    if len(good_bad) > 0:
        plt.scatter(
            good_bad["Circularity"],
            good_bad["Band4"],
            s=8,
            alpha=0.35,
            label="GOOD",
        )

    plt.scatter(
        good["Circularity"],
        good["Band4"],
        s=80,
        marker="x",
        linewidths=2,
        label="Known-good",
    )

    plt.axvline(
        CIRCULARITY_THRESHOLD,
        linestyle="--",
        linewidth=2,
    )

    plt.axhline(
        BAND4_THRESHOLD,
        linestyle="--",
        linewidth=2,
    )

    plt.xlabel("Circularity")
    plt.ylabel("Band 4 Pixel Count")
    plt.title("Classifier Feature Space: Circularity vs Band 4")
    plt.legend()
    plt.grid(alpha=0.25)

    plt.tight_layout()

    output_path = os.path.join(
        output_dir,
        "classifier_feature_space.png",
    )

    plt.savefig(output_path, dpi=200)
    plt.close()

    print(output_path)

    print()
    print("=" * 80)
    print("2D FEATURE ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()