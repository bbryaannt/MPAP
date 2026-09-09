"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Batch Frame Processor Test
===============================================================================
"""

from pathlib import Path

from pipeline.batch_processor import BatchProcessor


def main():

    folder = input(
        "Enter the path to an RPM222XR frame folder: "
    ).strip()

    if not folder:
        print("No folder provided.")
        return

    processor = BatchProcessor()

    results = processor.process_folder(
        Path(folder)
    )

    print("=" * 40)
    print("Batch Processor Test")
    print("=" * 40)
    print()

    print("Frames Processed:", len(results))
    print()

    for result in results[:10]:
        print(
            f"Frame {result.frame_number}: "
            f"{result.filename} -> "
            f"{result.classification.value}"
        )

    if len(results) > 10:
        print()
        print(
            f"... {len(results) - 10} additional frames"
        )

    print()

    counts = {}

    for result in results:
        classification = result.classification.value
        counts[classification] = (
            counts.get(classification, 0) + 1
        )

    print("Classification Counts:")

    for classification, count in sorted(
        counts.items()
    ):
        print(
            f"  {classification}: {count}"
        )


if __name__ == "__main__":
    main()