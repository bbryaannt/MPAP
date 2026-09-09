from pathlib import Path
from collections import defaultdict
import statistics

from pipeline.batch_processor import BatchProcessor


DATASETS = {
    "GOOD": "/Volumes/Army Research Lab/dat Files/test_1_good_images",
    "TOO_FAST": "/Volumes/Army Research Lab/dat Files/test_2_too_fast_images",
    "LOW_POWER": "/Volumes/Army Research Lab/dat Files/test_3_too_low_power_images",
    "LOW_POWDER": "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder",
    "TOO_SLOW": "/Volumes/Army Research Lab/dat Files/test_5_too_slow_images",
    "HIGH_POWER": "/Volumes/Army Research Lab/dat Files/test_6_too_high_power",
}


def summarize(name, results):
    active = [
        r for r in results
        if r.classification.value != "LASER_OFF"
    ]

    if not active:
        print(f"\n{name}: NO ACTIVE FRAMES")
        return

    features = {
        "Area mm2": [r.features.area_mm2 for r in active],
        "B3": [r.band_counts.band3 for r in active],
        "B4": [r.band_counts.band4 for r in active],
        "B5": [r.band_counts.band5 for r in active],
        "Circularity": [r.features.circularity for r in active],
        "BBox Width": [r.features.bbox_width for r in active],
        "BBox Height": [r.features.bbox_height for r in active],
        "Aspect Ratio": [r.features.aspect_ratio for r in active],
    }

    print("\n" + "=" * 75)
    print(f"{name}")
    print(f"Active frames: {len(active)}")
    print("=" * 75)

    print(
        f"{'Feature':<18}"
        f"{'Mean':>12}"
        f"{'Std':>12}"
        f"{'Min':>12}"
        f"{'Max':>12}"
    )

    print("-" * 75)

    for feature_name, values in features.items():
        print(
            f"{feature_name:<18}"
            f"{statistics.mean(values):>12.3f}"
            f"{statistics.stdev(values) if len(values) > 1 else 0:>12.3f}"
            f"{min(values):>12.3f}"
            f"{max(values):>12.3f}"
        )


def main():
    processor = BatchProcessor()

    for name, folder in DATASETS.items():
        print(f"\nProcessing {name}...")
        results = processor.process_folder(Path(folder))
        summarize(name, results)


if __name__ == "__main__":
    main()
