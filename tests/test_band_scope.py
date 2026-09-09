"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Band Scope Diagnostic
===============================================================================

Purpose:
    Determine whether the thermal-band counts used by the classifier are
    actually describing the detected melt pool or the surrounding thermal
    field.

This diagnostic DOES NOT modify the MPAP pipeline.

It compares:

    1. Full image thermal-band counts
    2. Central ROI thermal-band counts
    3. Detected melt-pool-mask thermal-band counts

It also reports:

    - Peak temperature
    - Detection threshold
    - Raw detected-mask pixels
    - Cleaned melt-pool features
    - Area
    - Circularity
    - Band 3
    - Band 4
    - Band 5

Known datasets:
    GOOD:
        /Volumes/Army Research Lab/dat Files/test_1_good_images

    LOW POWDER:
        /Volumes/Army Research Lab/dat Files/test_4_too_low_powder

IMPORTANT:
    The actual MPAP pipeline is used for decoding and feature extraction.
    This avoids duplicating the RPM222XR .dat decoding logic.
===============================================================================
"""

from pathlib import Path

import cv2
import numpy as np

from config import config
from pipeline.pipeline import MeltPoolPipeline
from pipeline.melt_pool_features import MeltPoolFeatureExtractor


# =============================================================================
# DATASET PATHS
# =============================================================================

GOOD_FOLDER = Path(
    "/Volumes/Army Research Lab/dat Files/test_1_good_images"
)

LOW_POWDER_FOLDER = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)


# =============================================================================
# THERMAL BAND DEFINITIONS
# =============================================================================

B3_LOW = 38200
B3_HIGH = 43800

B4_LOW = 43800
B4_HIGH = 49400

B5_LOW = 49400


# =============================================================================
# DETECTOR ROI
# =============================================================================

ROI_HALF_HEIGHT = 120
ROI_HALF_WIDTH = 250


# =============================================================================
# KNOWN UNKNOWN FRAMES
#
# These are the frame numbers reported by the existing BatchProcessor.
#
# IMPORTANT:
# BatchProcessor uses zero-based frame numbers while filenames begin at
# Image000001.dat.
#
# Therefore:
#
#     reported frame 882 -> Image000883.dat
#     reported frame 883 -> Image000884.dat
#     reported frame 884 -> Image000885.dat
#     reported frame 4459 -> Image004460.dat
# =============================================================================

UNKNOWN_FRAME_NUMBERS = [
    882,
    883,
    884,
    1184,
    1185,
    1771,
    2067,
    2367,
    2951,
    3252,
    3253,
    3548,
    4152,
    4459,
]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def count_bands(image: np.ndarray) -> tuple[int, int, int]:
    """
    Count B3, B4, and B5 pixels in an image.

    B3:
        38200 <= value < 43800

    B4:
        43800 <= value < 49400

    B5:
        value >= 49400
    """

    values = image.astype(np.int64)

    band3 = int(
        np.count_nonzero(
            (values >= B3_LOW)
            & (values < B3_HIGH)
        )
    )

    band4 = int(
        np.count_nonzero(
            (values >= B4_LOW)
            & (values < B4_HIGH)
        )
    )

    band5 = int(
        np.count_nonzero(
            values >= B5_LOW
        )
    )

    return band3, band4, band5


def crop_central_roi(image: np.ndarray) -> np.ndarray:
    """
    Return the same central ROI used by the melt-pool detector.
    """

    height, width = image.shape

    cx = width // 2
    cy = height // 2

    x1 = max(
        0,
        cx - ROI_HALF_WIDTH,
    )

    x2 = min(
        width,
        cx + ROI_HALF_WIDTH,
    )

    y1 = max(
        0,
        cy - ROI_HALF_HEIGHT,
    )

    y2 = min(
        height,
        cy + ROI_HALF_HEIGHT,
    )

    return image[y1:y2, x1:x2]


def clean_mask_for_band_analysis(
    mask: np.ndarray,
    minimum_component_area: int,
    morphology_kernel_size: int = 5,
) -> np.ndarray:
    """
    Reproduce the mask-cleaning behavior used by
    MeltPoolFeatureExtractor.

    This is used only for the diagnostic.
    """

    binary = (
        mask.astype(np.uint8) * 255
    )

    num_labels, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            binary,
            connectivity=8,
        )
    )

    cleaned = np.zeros_like(binary)

    for label in range(1, num_labels):

        area = stats[
            label,
            cv2.CC_STAT_AREA,
        ]

        if area >= minimum_component_area:

            cleaned[
                labels == label
            ] = 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (
            morphology_kernel_size,
            morphology_kernel_size,
        ),
    )

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_CLOSE,
        kernel,
    )

    return cleaned


def get_detected_mask(
    image: np.ndarray,
) -> tuple[np.ndarray, float, int]:
    """
    Reproduce the melt-pool detection calculation used by MPAP.

    Returns:

        mask
        threshold
        raw_signal_pixels
    """

    roi = crop_central_roi(image)

    peak = float(
        np.max(roi)
    )

    threshold = peak * config.detection.peak_fraction

    raw_mask = (
        roi >= threshold
    ).astype(np.uint8)

    raw_signal_pixels = int(
        np.count_nonzero(raw_mask)
    )

    # Put ROI mask back into full-image coordinates.
    full_mask = np.zeros_like(
        image,
        dtype=np.uint8,
    )

    height, width = image.shape

    cx = width // 2
    cy = height // 2

    x1 = max(
        0,
        cx - ROI_HALF_WIDTH,
    )

    x2 = min(
        width,
        cx + ROI_HALF_WIDTH,
    )

    y1 = max(
        0,
        cy - ROI_HALF_HEIGHT,
    )

    y2 = min(
        height,
        cy + ROI_HALF_HEIGHT,
    )

    full_mask[
        y1:y2,
        x1:x2,
    ] = raw_mask

    return (
        full_mask,
        threshold,
        raw_signal_pixels,
    )


def get_largest_cleaned_component(
    mask: np.ndarray,
) -> np.ndarray:
    """
    Return only the largest connected component after the same
    cleaning operation used by MeltPoolFeatureExtractor.
    """

    cleaned = clean_mask_for_band_analysis(
        mask,
        minimum_component_area=(
            config.detection.min_component_area
        ),
        morphology_kernel_size=5,
    )

    contours, _ = cv2.findContours(
        cleaned,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE,
    )

    if not contours:
        return np.zeros_like(
            mask,
            dtype=np.uint8,
        )

    largest = max(
        contours,
        key=cv2.contourArea,
    )

    largest_mask = np.zeros_like(
        mask,
        dtype=np.uint8,
    )

    cv2.drawContours(
        largest_mask,
        [largest],
        -1,
        1,
        thickness=-1,
    )

    return largest_mask


def print_band_counts(
    label: str,
    image: np.ndarray,
) -> tuple[int, int, int]:

    band3, band4, band5 = count_bands(
        image
    )

    print(
        f"{label:<28}"
        f"B3={band3:<6} "
        f"B4={band4:<6} "
        f"B5={band5:<6}"
    )

    return (
        band3,
        band4,
        band5,
    )


# =============================================================================
# PROCESS ONE FRAME
# =============================================================================

def analyze_frame(
    path: Path,
    label: str,
    frame_number: int | None = None,
) -> None:

    print()
    print("-" * 90)

    if frame_number is not None:

        print(
            f"{label} | "
            f"Reported Frame {frame_number} | "
            f"{path.name}"
        )

    else:

        print(
            f"{label} | "
            f"{path.name}"
        )

    print("-" * 90)

    # -------------------------------------------------------------------------
    # Use the actual MPAP pipeline decoder.
    #
    # MeltPoolPipeline.process_file() performs the normal MPAP decode,
    # detection, feature extraction, band counting, and classification.
    # -------------------------------------------------------------------------

    pipeline = MeltPoolPipeline()

    result = pipeline.process_file(
        str(path)
    )

    # -------------------------------------------------------------------------
    # The pipeline result contains the measurements we already calculate.
    # -------------------------------------------------------------------------

    features = result.features
    pipeline_bands = result.band_counts
    classification = result.classification

    print()
    print("MPAP PIPELINE RESULT")
    print(
        f"Classification       : "
        f"{classification.value}"
    )

    print(
        f"Area (px)            : "
        f"{features.area_px:.2f}"
    )

    print(
        f"Area (mm^2)          : "
        f"{features.area_mm2:.4f}"
    )

    print(
        f"Centroid             : "
        f"({features.centroid_x:.2f}, "
        f"{features.centroid_y:.2f})"
    )

    print(
        f"Bounding box         : "
        f"{features.bbox_width} x "
        f"{features.bbox_height}"
    )

    print(
        f"Aspect ratio         : "
        f"{features.aspect_ratio:.4f}"
    )

    print(
        f"Circularity          : "
        f"{features.circularity:.6f}"
    )

    print()
    print("BANDS USED BY CURRENT PIPELINE")

    print(
        f"B3                    : "
        f"{pipeline_bands.band3}"
    )

    print(
        f"B4                    : "
        f"{pipeline_bands.band4}"
    )

    print(
        f"B5                    : "
        f"{pipeline_bands.band5}"
    )

    # -------------------------------------------------------------------------
    # IMPORTANT:
    #
    # The existing pipeline result does not expose the decoded image.
    #
    # Therefore this diagnostic imports the project's decoder dynamically
    # instead of implementing a second RPM222XR decoder.
    # -------------------------------------------------------------------------

    try:

        from pipeline.decoder import RPM222XRDecoder

    except ImportError as exc:

        print()
        print(
            "ERROR: Could not import "
            "RPM222XRDecoder from pipeline.decoder."
        )

        print()
        print(
            "The existing MPAP decoder API is different "
            "from the expected API."
        )

        print(
            f"Import error: {exc}"
        )

        raise

    decoder = RPM222XRDecoder()

    decoded = decoder.decode(
        str(path)
    )

    image = decoded.image

    if image.ndim != 2:

        raise ValueError(
            "Decoded thermal image must be 2-D."
        )

    # -------------------------------------------------------------------------
    # IMAGE INFORMATION
    # -------------------------------------------------------------------------

    print()
    print("DECODED IMAGE")

    print(
        f"Shape                : "
        f"{image.shape}"
    )

    print(
        f"Data type            : "
        f"{image.dtype}"
    )

    print(
        f"Minimum pixel        : "
        f"{int(np.min(image))}"
    )

    print(
        f"Maximum pixel        : "
        f"{int(np.max(image))}"
    )

    # -------------------------------------------------------------------------
    # PEAK / DETECTION
    # -------------------------------------------------------------------------

    roi = crop_central_roi(
        image
    )

    peak = int(
        np.max(roi)
    )

    threshold = (
        peak *
        config.detection.peak_fraction
    )

    print()
    print("DETECTION")

    print(
        f"ROI peak             : "
        f"{peak}"
    )

    print(
        f"Peak fraction        : "
        f"{config.detection.peak_fraction}"
    )

    print(
        f"Detection threshold  : "
        f"{threshold:.2f}"
    )

    # -------------------------------------------------------------------------
    # FULL IMAGE
    # -------------------------------------------------------------------------

    print()
    print("THERMAL BAND SCOPE")

    print(
        f"{'Scope':<28}"
        f"B3={'':<5} "
        f"B4={'':<5} "
        f"B5={'':<5}"
    )

    print_band_counts(
        "Full image",
        image,
    )

    # -------------------------------------------------------------------------
    # CENTRAL ROI
    # -------------------------------------------------------------------------

    print_band_counts(
        "Central detector ROI",
        roi,
    )

    # -------------------------------------------------------------------------
    # DETECTED RAW MASK
    # -------------------------------------------------------------------------

    raw_mask, threshold, raw_signal_pixels = (
        get_detected_mask(image)
    )

    raw_detected_values = image[
        raw_mask.astype(bool)
    ]

    if raw_detected_values.size > 0:

        print_band_counts(
            "Raw detected mask",
            raw_detected_values,
        )

    else:

        print(
            f"{'Raw detected mask':<28}"
            "B3=0      "
            "B4=0      "
            "B5=0"
        )

    print(
        f"Raw signal pixels     : "
        f"{raw_signal_pixels}"
    )

    # -------------------------------------------------------------------------
    # CLEANED / LARGEST MELT POOL
    # -------------------------------------------------------------------------

    largest_mask = (
        get_largest_cleaned_component(
            raw_mask
        )
    )

    cleaned_pixels = int(
        np.count_nonzero(
            largest_mask
        )
    )

    cleaned_values = image[
        largest_mask.astype(bool)
    ]

    if cleaned_values.size > 0:

        print_band_counts(
            "Largest cleaned pool",
            cleaned_values,
        )

    else:

        print(
            f"{'Largest cleaned pool':<28}"
            "B3=0      "
            "B4=0      "
            "B5=0"
        )

    print(
        f"Cleaned pool pixels   : "
        f"{cleaned_pixels}"
    )

    # -------------------------------------------------------------------------
    # COMPARE THE PIPELINE BAND COUNTS TO MASK BAND COUNTS
    # -------------------------------------------------------------------------

    mask_b3, mask_b4, mask_b5 = (
        count_bands(cleaned_values)
        if cleaned_values.size > 0
        else (0, 0, 0)
    )

    print()
    print("COMPARISON")

    print(
        f"Pipeline B3          : "
        f"{pipeline_bands.band3}"
    )

    print(
        f"Mask B3              : "
        f"{mask_b3}"
    )

    print(
        f"Difference B3        : "
        f"{pipeline_bands.band3 - mask_b3}"
    )

    print()

    print(
        f"Pipeline B4          : "
        f"{pipeline_bands.band4}"
    )

    print(
        f"Mask B4              : "
        f"{mask_b4}"
    )

    print(
        f"Difference B4        : "
        f"{pipeline_bands.band4 - mask_b4}"
    )

    print()

    print(
        f"Pipeline B5          : "
        f"{pipeline_bands.band5}"
    )

    print(
        f"Mask B5              : "
        f"{mask_b5}"
    )

    print(
        f"Difference B5        : "
        f"{pipeline_bands.band5 - mask_b5}"
    )


# =============================================================================
# FIND GOOD FRAMES
# =============================================================================

def find_good_frames(
    folder: Path,
    number_to_find: int = 5,
) -> list[tuple[int, Path]]:

    print(
        f"Searching for "
        f"{number_to_find} GOOD frames..."
    )

    if not folder.exists():

        raise FileNotFoundError(
            f"Folder does not exist:\n{folder}"
        )

    files = sorted(
        folder.glob("*.dat")
    )

    if not files:

        raise FileNotFoundError(
            f"No .dat files found in:\n{folder}"
        )

    pipeline = MeltPoolPipeline()

    good_frames = []

    for frame_number, path in enumerate(files):

        try:

            result = pipeline.process_file(
                str(path)
            )

        except Exception as exc:

            print(
                f"Skipping {path.name}: "
                f"{exc}"
            )

            continue

        if result.classification.value == "GOOD":

            good_frames.append(
                (
                    frame_number,
                    path,
                )
            )

            if len(good_frames) >= number_to_find:

                break

    return good_frames


# =============================================================================
# FIND FILE FOR REPORTED FRAME NUMBER
# =============================================================================

def reported_frame_to_path(
    folder: Path,
    frame_number: int,
) -> Path:

    """
    Convert the BatchProcessor's zero-based frame number into the
    corresponding sorted .dat filename.

    Example:

        frame 882
        -> sorted file index 882
        -> Image000883.dat
    """

    files = sorted(
        folder.glob("*.dat")
    )

    if frame_number < 0:

        raise ValueError(
            "Frame number cannot be negative."
        )

    if frame_number >= len(files):

        raise IndexError(
            f"Reported frame {frame_number} "
            f"does not exist in {folder}. "
            f"Folder contains {len(files)} frames."
        )

    return files[
        frame_number
    ]


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 90)

    print(
        "MPAP BAND SCOPE DIAGNOSTIC"
    )

    print("=" * 90)

    print()
    print(
        "This diagnostic does NOT modify "
        "the MPAP pipeline."
    )

    print()
    print("Thermal bands:")

    print(
        "B3 = 38200-43799"
    )

    print(
        "B4 = 43800-49399"
    )

    print(
        "B5 = 49400+"
    )

    # =========================================================================
    # KNOWN GOOD DATASET
    # =========================================================================

    print()
    print("=" * 90)

    print(
        "KNOWN GOOD DATASET"
    )

    print("=" * 90)

    good_frames = find_good_frames(
        GOOD_FOLDER,
        number_to_find=5,
    )

    print()
    print(
        f"Selected {len(good_frames)} "
        f"GOOD frames."
    )

    for frame_number, path in good_frames:

        analyze_frame(
            path=path,
            label="KNOWN GOOD",
            frame_number=frame_number,
        )

    # =========================================================================
    # UNKNOWN FRAMES
    # =========================================================================

    print()
    print("=" * 90)

    print(
        "UNKNOWN CANDIDATE FRAMES"
    )

    print("=" * 90)

    print()
    print(
        f"Analyzing "
        f"{len(UNKNOWN_FRAME_NUMBERS)} "
        f"previously UNKNOWN frames."
    )

    for frame_number in UNKNOWN_FRAME_NUMBERS:

        path = reported_frame_to_path(
            LOW_POWDER_FOLDER,
            frame_number,
        )

        analyze_frame(
            path=path,
            label="UNKNOWN CANDIDATE",
            frame_number=frame_number,
        )

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print()
    print("=" * 90)

    print(
        "DIAGNOSTIC COMPLETE"
    )

    print("=" * 90)

    print()
    print(
        "The important comparison is:"
    )

    print()
    print(
        "Pipeline B3/B4/B5"
        "  versus"
        "  Largest cleaned pool B3/B4/B5"
    )

    print()
    print(
        "If the pipeline values are much larger "
        "than the melt-pool-mask values, then "
        "the current ThermalBandCounter is "
        "measuring the surrounding thermal field "
        "rather than the detected melt pool."
    )

    print()


if __name__ == "__main__":
    main()
