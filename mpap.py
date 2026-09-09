"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Unified Dataset Analysis Entry Point
===============================================================================
"""

import subprocess
import sys
from pathlib import Path


# =============================================================================
# HELPERS
# =============================================================================

def print_header(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def run_step(title, command):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)
    print()

    result = subprocess.run(command)

    if result.returncode != 0:
        print()
        print("=" * 72)
        print(f"ERROR: {title} failed.")
        print("=" * 72)
        print()

        sys.exit(result.returncode)


# =============================================================================
# MAIN
# =============================================================================

def main():

    if len(sys.argv) != 2:
        print()
        print("Usage:")
        print('python mpap.py "/path/to/dat/folder"')
        print()
        sys.exit(1)

    dataset_folder = Path(sys.argv[1])

    # -------------------------------------------------------------------------
    # Validate dataset folder
    # -------------------------------------------------------------------------

    if not dataset_folder.exists():
        print()
        print("ERROR: Dataset folder does not exist:")
        print(dataset_folder)
        print()
        sys.exit(1)

    if not dataset_folder.is_dir():
        print()
        print("ERROR: Dataset path is not a directory:")
        print(dataset_folder)
        print()
        sys.exit(1)

    dat_files = sorted(dataset_folder.glob("*.dat"))

    if not dat_files:
        print()
        print("ERROR: No .dat files were found in:")
        print(dataset_folder)
        print()
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------

    print_header("MPAP DATASET ANALYSIS")

    print()
    print("Dataset:")
    print(dataset_folder)

    print()
    print("DAT files found:", len(dat_files))

    # -------------------------------------------------------------------------
    # STEP 1 — Batch processing
    # -------------------------------------------------------------------------

    run_step(
        "STEP 1/3 — FRAME-LEVEL PROCESSING",
        [
            sys.executable,
            "-m",
            "pipeline.batch_processor",
            str(dataset_folder),
        ],
    )

    # -------------------------------------------------------------------------
    # Verify diagnostic CSV
    # -------------------------------------------------------------------------

    diagnostic_csv = (
        dataset_folder /
        "classification_diagnostic.csv"
    )

    if not diagnostic_csv.exists():
        print()
        print("ERROR: Batch processor did not create:")
        print(diagnostic_csv)
        print()
        sys.exit(1)

    # -------------------------------------------------------------------------
    # STEP 2 — Layer analysis
    # -------------------------------------------------------------------------

    run_step(
        "STEP 2/3 — LAYER ANALYSIS",
        [
            sys.executable,
            "analyze_classification.py",
            str(dataset_folder),
        ],
    )

    # -------------------------------------------------------------------------
    # STEP 3 — Dataset report
    # -------------------------------------------------------------------------

    run_step(
        "STEP 3/3 — DATASET REPORT",
        [
            sys.executable,
            "dataset_report.py",
            str(dataset_folder),
        ],
    )

    # -------------------------------------------------------------------------
    # Verify outputs
    # -------------------------------------------------------------------------

    output_files = [
        dataset_folder / "classification_diagnostic.csv",
        dataset_folder / "layer_trend_analysis.csv",
        dataset_folder / "layer_classification_analysis.csv",
        dataset_folder / "dataset_report.txt",
        dataset_folder / "dataset_summary.csv",
    ]

    # -------------------------------------------------------------------------
    # Final summary
    # -------------------------------------------------------------------------

    print_header("MPAP ANALYSIS COMPLETE")

    print()
    print("Dataset:")
    print(dataset_folder)

    print()
    print("Output files:")

    for output_file in output_files:
        if output_file.exists():
            print(f"  ✓ {output_file}")
        else:
            print(f"  - {output_file} (not generated)")

    print()
    print("=" * 72)
    print("All MPAP analysis stages completed successfully.")
    print("=" * 72)
    print()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()