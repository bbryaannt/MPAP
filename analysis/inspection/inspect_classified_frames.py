"""
MPAP

Classified Frame Visual Inspection

Selects representative frames from each frame-level classification
and saves the original thermal image beside its melt-pool mask.

The representative frame is selected using distance from the mean
feature values within each classification group.
"""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from pipeline.pipeline import MeltPoolPipeline


CLASSIFICATION_ORDER = [
    "GOOD",
    "LOW_POWDER",
    "LOW_POWER",
    "HIGH_POWER",
    "UNKNOWN",
]


def record_feature_vector(record):
    """Return the feature vector used for frame selection."""

    result = record["result"]
    features = result.features
    bands = result.band_counts

    return {
        "area_mm2": float(features.area_mm2),
        "circularity": float(features.circularity),
        "band3": float(bands.band3),
        "band4": float(bands.band4),
        "band5": float(bands.band5),
    }


def choose_representative_frame(records):
    """
    Select the frame closest to the mean feature vector for a
    classification group.
    """

    if not records:
        return None

    feature_names = [
        "area_mm2",
        "circularity",
        "band3",
        "band4",
        "band5",
    ]

    vectors = [
        record_feature_vector(record)
        for record in records
    ]

    means = {}

    for name in feature_names:
        values = [
            vector[name]
            for vector in vectors
        ]

        means[name] = sum(values) / len(values)

    scales = {}

    for name in feature_names:
        scale = abs(means[name])

        if scale < 1e-12:
            scale = 1.0

        scales[name] = scale

    best_record = None
    best_distance = None

    for record, vector in zip(records, vectors):

        distance = 0.0

        for name in feature_names:

            difference = (
                vector[name]
                - means[name]
            )

            normalized = (
                difference
                / scales[name]
            )

            distance += normalized ** 2

        if (
            best_distance is None
            or distance < best_distance
        ):
            best_distance = distance
            best_record = record

    return best_record


def process_dataset(dataset_path):
    """Process one dataset and save representative frames."""

    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset does not exist: {dataset_path}"
        )

    dat_files = sorted(
        dataset_path.glob("*.dat")
    )

    if not dat_files:
        raise RuntimeError(
            f"No .dat files found in: {dataset_path}"
        )

    print()
    print("=" * 72)
    print("MPAP CLASSIFIED FRAME VISUAL INSPECTION")
    print("=" * 72)
    print(f"Dataset: {dataset_path}")
    print(f"Frames:  {len(dat_files)}")
    print()

    pipeline = MeltPoolPipeline()

    records_by_classification = {
        classification: []
        for classification in CLASSIFICATION_ORDER
    }

    print("Processing frames...")

    for frame_index, path in enumerate(dat_files):

        if frame_index % 500 == 0:
            print(
                f"  Processed "
                f"{frame_index}/{len(dat_files)}"
            )

        decoded = pipeline.decoder.decode(
            str(path)
        )

        result = pipeline.process_decoded(
            decoded,
            frame_number=frame_index,
        )

        classification = (
            result.classification.value
        )

        if (
            classification
            not in records_by_classification
        ):
            records_by_classification[
                classification
            ] = []

        records_by_classification[
            classification
        ].append(
            {
                "frame_index": frame_index,
                "filename": path.name,
                "classification": classification,
                "decoded": decoded,
                "result": result,
            }
        )

    print(
        f"  Processed "
        f"{len(dat_files)}/{len(dat_files)}"
    )

    print()
    print("Classification counts:")

    for classification in CLASSIFICATION_ORDER:

        count = len(
            records_by_classification.get(
                classification,
                [],
            )
        )

        if count:
            print(
                f"  {classification:<12} "
                f"{count}"
            )

    output_root = (
        dataset_path
        / "visual_inspection"
    )

    print()
    print("Selecting representative frames...")

    for classification in CLASSIFICATION_ORDER:

        records = (
            records_by_classification.get(
                classification,
                [],
            )
        )

        if not records:
            continue

        representative = (
            choose_representative_frame(
                records
            )
        )

        if representative is None:
            continue

        frame_index = (
            representative["frame_index"]
        )

        filename = (
            representative["filename"]
        )

        decoded = (
            representative["decoded"]
        )

        result = (
            representative["result"]
        )

        mask = (
            pipeline.detector
            .threshold_from_peak(
                decoded,
                peak_fraction=(
                    pipeline.peak_fraction
                ),
            )
        )

        output_dir = (
            output_root
            / classification
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_dir
            / f"frame_{frame_index:06d}.png"
        )

        features = result.features
        bands = result.band_counts

        figure = plt.figure(
            figsize=(16, 8)
        )

        ax1 = figure.add_subplot(2, 2, 1)

        ax1.imshow(
            decoded.image,
            cmap="gray",
        )

        ax1.set_title(
            f"Frame {frame_index} - Original\n"
            f"Classification: {classification}"
        )

        ax1.axis("off")

        ax2 = figure.add_subplot(2, 2, 2)

        ax2.imshow(
            mask,
            cmap="gray",
        )

        ax2.set_title(
            "Melt Pool Mask\n"
            f"{classification}"
        )

        ax2.axis("off")

        ax3 = figure.add_subplot(2, 2, 3)

        ax3.axis("off")

        feature_text = (
            f"File: {filename}\n"
            f"Frame: {frame_index}\n"
            f"Classification: "
            f"{classification}\n"
            "\n"
            f"Area: "
            f"{features.area_mm2:.4f} mm²\n"
            f"Circularity: "
            f"{features.circularity:.4f}\n"
            f"Aspect ratio: "
            f"{features.aspect_ratio:.4f}\n"
            f"BBox: "
            f"{features.bbox_width} × "
            f"{features.bbox_height} px\n"
            f"Centroid: "
            f"({features.centroid_x:.1f}, "
            f"{features.centroid_y:.1f})\n"
            "\n"
            f"Band 3: "
            f"{bands.band3:.1f}\n"
            f"Band 4: "
            f"{bands.band4:.1f}\n"
            f"Band 5: "
            f"{bands.band5:.1f}"
        )

        ax3.text(
            0.02,
            0.98,
            feature_text,
            transform=ax3.transAxes,
            verticalalignment="top",
            fontsize=12,
            family="monospace",
        )

        ax4 = figure.add_subplot(2, 2, 4)

        ax4.axis("off")

        if classification == "GOOD":

            rule_text = (
                "GOOD\n\n"
                "Thermal intensity is developed enough\n"
                "and melt-pool geometry meets the\n"
                "minimum circularity requirement."
            )

        elif classification == "LOW_POWDER":

            rule_text = (
                "LOW_POWDER\n\n"
                "Thermal intensity is sufficiently developed,\n"
                "but melt-pool geometry is insufficiently\n"
                "circular."
            )

        elif classification == "LOW_POWER":

            rule_text = (
                "LOW_POWER\n\n"
                "Thermal intensity has not reached the\n"
                "required GOOD range."
            )

        elif classification == "HIGH_POWER":

            rule_text = (
                "HIGH_POWER\n\n"
                "Band 5 exceeds the configured high-power\n"
                "threshold."
            )

        elif classification == "UNKNOWN":

            rule_text = (
                "UNKNOWN\n\n"
                "Frame does not satisfy any configured\n"
                "classification rule."
            )

        else:

            rule_text = (
                f"{classification}\n\n"
                "No classification explanation is configured."
            )

        ax4.text(
            0.02,
            0.98,
            rule_text,
            transform=ax4.transAxes,
            verticalalignment="top",
            fontsize=12,
        )

        figure.suptitle(
            "MPAP Visual Inspection - "
            f"{classification} - "
            f"Frame {frame_index}",
            fontsize=16,
        )

        figure.tight_layout(
            rect=(0, 0, 1, 0.95)
        )

        figure.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(figure)

        print(
            f"{classification:<12} "
            f"Frame {frame_index:6d} -> "
            f"{output_path}"
        )

    print()
    print("=" * 72)
    print("VISUAL INSPECTION COMPLETE")
    print("=" * 72)
    print(f"Output: {output_root}")
    print()


def main():

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "  python "
            "inspect_classified_frames.py "
            "\"/path/to/dataset\""
        )

        sys.exit(1)

    process_dataset(
        sys.argv[1]
    )


if __name__ == "__main__":
    main()
