from pathlib import Path

import matplotlib.pyplot as plt

from pipeline.pipeline import MeltPoolPipeline


DATASET = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)

# These are ACTUAL frame numbers, matching classification_diagnostic.csv.
FRAMES = [8616, 8617, 8618, 8619, 8620, 8621]

OUTPUT = DATASET / "visual_inspection" / "TRANSIENT_8617_8618"
OUTPUT.mkdir(parents=True, exist_ok=True)

files = sorted(DATASET.glob("*.dat"))

pipeline = MeltPoolPipeline()


def frame_to_file(frame_number):
    """Convert 1-based frame number to the corresponding sorted file."""
    index = frame_number - 1

    if index < 0 or index >= len(files):
        raise IndexError(
            f"Frame {frame_number} is outside the dataset."
        )

    return files[index]


for frame_number in FRAMES:

    path = frame_to_file(frame_number)

    # Use the exact same pipeline entry point used by the
    # classification diagnostic generation.
    result = pipeline.process_file(str(path))

    decoded = pipeline.decoder.decode(str(path))

    mask = pipeline.detector.threshold_from_peak(
        decoded,
        peak_fraction=0.85,
    )

    image = decoded.image

    classification = result.classification.value

    print(
        f"Frame {frame_number:5d} | "
        f"File {path.name:15s} | "
        f"{classification:11s} | "
        f"Area {result.features.area_mm2:7.4f} | "
        f"Cir {result.features.circularity:.4f} | "
        f"B3 {result.band_counts.band3:5d} | "
        f"B4 {result.band_counts.band4:4d}"
    )

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.imshow(image, cmap="gray")
    plt.title(
        f"Frame {frame_number} — {classification}"
    )
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.imshow(mask, cmap="gray")
    plt.title("Melt Pool Mask")
    plt.axis("off")

    plt.tight_layout()

    output_path = OUTPUT / f"frame_{frame_number:06d}.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    print(f"    Saved: {output_path}")


print()
print("=" * 80)
print("TRANSIENT SEQUENCE COMPLETE")
print("=" * 80)
print(f"Output: {OUTPUT}")
