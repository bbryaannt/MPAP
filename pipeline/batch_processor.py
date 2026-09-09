"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Batch Processor
===============================================================================
"""

from dataclasses import dataclass
from pathlib import Path
import csv
import sys

from pipeline.pipeline import MeltPoolPipeline
from pipeline.classifier import MeltPoolClassification
from pipeline.melt_pool_features import MeltPoolFeatures
from models.band_counts import BandCounts


@dataclass
class BatchResult:
    frame_number: int
    filename: str
    features: MeltPoolFeatures
    band_counts: BandCounts
    classification: MeltPoolClassification


class BatchProcessor:
    def __init__(self, pipeline=None):
        self.pipeline = (
            pipeline
            if pipeline is not None
            else MeltPoolPipeline()
        )

    def process_folder(self, folder):
        folder = Path(folder)

        if not folder.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder}")

        if not folder.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder}")

        files = sorted(folder.glob("*.dat"))

        if not files:
            return []

        results = []

        for frame_number, path in enumerate(files, start=1):
            result = self.pipeline.process_file(str(path))

            results.append(
                BatchResult(
                    frame_number=frame_number,
                    filename=path.name,
                    features=result.features,
                    band_counts=result.band_counts,
                    classification=result.classification,
                )
            )

        return results

    def export_csv(self, results, output_path):
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fieldnames = [
            "Frame",
            "Filename",
            "Classification",
            "Area_px",
            "Area_mm2",
            "Centroid_X",
            "Centroid_Y",
            "BBox_Width",
            "BBox_Height",
            "Aspect_Ratio",
            "Circularity",
            "Band1",
            "Band2",
            "Band3",
            "Band4",
            "Band5",
        ]

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for result in results:
                features = result.features
                bands = result.band_counts

                writer.writerow(
                    {
                        "Frame": result.frame_number,
                        "Filename": result.filename,
                        "Classification": result.classification.value,
                        "Area_px": features.area_px,
                        "Area_mm2": features.area_mm2,
                        "Centroid_X": features.centroid_x,
                        "Centroid_Y": features.centroid_y,
                        "BBox_Width": features.bbox_width,
                        "BBox_Height": features.bbox_height,
                        "Aspect_Ratio": features.aspect_ratio,
                        "Circularity": features.circularity,
                        "Band1": bands.band1,
                        "Band2": bands.band2,
                        "Band3": bands.band3,
                        "Band4": bands.band4,
                        "Band5": bands.band5,
                    }
                )


def print_summary(results):
    print()
    print("-" * 72)
    print("CLASSIFICATION SUMMARY")
    print("-" * 72)

    counts = {
        classification: 0
        for classification in MeltPoolClassification
    }

    for result in results:
        counts[result.classification] += 1

    for classification in MeltPoolClassification:
        print(
            f"{classification.value:<18}"
            f"{counts[classification]:>6}"
        )

    print("-" * 72)
    print(f"{'TOTAL':<18}{len(results):>6}")
    print("-" * 72)


def main():
    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "python -m pipeline.batch_processor "
            '"/path/to/dat/folder"'
        )
        sys.exit(1)

    folder = Path(sys.argv[1])

    print()
    print("=" * 72)
    print("MPAP BATCH PROCESSOR")
    print("=" * 72)
    print(f"Folder: {folder}")
    print()
    print("Processing .dat files...")
    print()

    processor = BatchProcessor()
    results = processor.process_folder(folder)

    print_summary(results)

    output_path = folder / "classification_diagnostic.csv"

    processor.export_csv(
        results,
        output_path,
    )

    print()
    print(f"Diagnostic CSV:")
    print(output_path)
    print("=" * 72)


if __name__ == "__main__":
    main()