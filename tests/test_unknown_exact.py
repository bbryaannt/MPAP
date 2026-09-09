from pathlib import Path

from pipeline.batch_processor import BatchProcessor


DATASET = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)


def main():

    print("=" * 100)
    print("MPAP EXACT UNKNOWN CHECK")
    print("=" * 100)
    print()

    processor = BatchProcessor()

    results = processor.process_folder(DATASET)

    print()
    print("=" * 100)
    print("RESULTS")
    print("=" * 100)

    counts = {}

    for result in results:
        label = str(result.classification)

        counts[label] = counts.get(label, 0) + 1

    print()
    print(f"Total frames: {len(results):,}")
    print()

    for label, count in counts.items():
        print(f"{label:20s}: {count:,}")

    unknown = [
        result
        for result in results
        if str(result.classification) == "MeltPoolClassification.UNKNOWN"
        or str(result.classification) == "UNKNOWN"
    ]

    print()
    print("=" * 100)
    print(f"UNKNOWN FRAMES: {len(unknown)}")
    print("=" * 100)

    for result in unknown:
        print(
            f"Frame {result.frame_number:5d} | "
            f"{result.filename} | "
            f"Area={result.features.area_mm2:.3f} mm2 | "
            f"B3={result.band_counts.band3:5d} | "
            f"B4={result.band_counts.band4:5d} | "
            f"B5={result.band_counts.band5:5d} | "
            f"Circ={result.features.circularity:.3f}"
        )


if __name__ == "__main__":
    main()