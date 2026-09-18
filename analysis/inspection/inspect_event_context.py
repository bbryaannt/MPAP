"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Transient Event Context Inspection
===============================================================================

Visually inspects representative LOW_POWDER transient events.

For each selected event:

    BEFORE -> TARGET EVENT -> AFTER

The event frame numbers come directly from transient_events.csv and are
treated as the actual ImageXXXXXX.dat numbering.

This script uses the existing MPAP pipeline for classification and feature
calculation.

It does not modify classifier thresholds or persistence logic.

===============================================================================
"""

from pathlib import Path
import math
import sys

# =============================================================================
# PROJECT ROOT
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# IMPORTS
# =============================================================================

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pipeline.pipeline import MeltPoolPipeline


# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)

INPUT_CSV = DATASET / "transient_events.csv"

OUTPUT_DIR = (
    DATASET
    / "visual_inspection"
    / "event_context"
)

MAX_EVENTS_PER_CATEGORY = 2

CONTEXT_BEFORE = 3
CONTEXT_AFTER = 3

MAX_TARGET_FRAMES_TO_DISPLAY = 12


# =============================================================================
# PIPELINE
# =============================================================================

pipeline = MeltPoolPipeline()


# =============================================================================
# HELPERS
# =============================================================================

def duration_category(duration):
    """Return the duration category for an event."""

    duration = int(duration)

    if duration == 1:
        return "1_FRAME"

    if duration == 2:
        return "2_FRAMES"

    if 3 <= duration <= 5:
        return "3_5_FRAMES"

    if 6 <= duration <= 10:
        return "6_10_FRAMES"

    if 11 <= duration <= 30:
        return "11_30_FRAMES"

    if 31 <= duration <= 60:
        return "31_60_FRAMES"

    return "61_PLUS_FRAMES"


def load_event_data():
    """Load transient event data."""

    if not INPUT_CSV.exists():

        raise FileNotFoundError(
            f"Could not find:\n{INPUT_CSV}"
        )

    events = pd.read_csv(
        INPUT_CSV
    )

    required_columns = {
        "Event_ID",
        "Layer",
        "Start_Frame",
        "End_Frame",
        "Duration_Frames",
        "Classification",
    }

    missing = (
        required_columns
        - set(events.columns)
    )

    if missing:

        raise ValueError(
            "transient_events.csv is missing columns: "
            f"{sorted(missing)}"
        )

    return events


# =============================================================================
# FRAME FILE LOOKUP
# =============================================================================

def find_frame_file(frame_number):
    """
    Find the .dat file corresponding to a diagnostic frame number.

    IMPORTANT:

    transient_events.csv uses the same frame numbering as the ImageXXXXXX.dat
    files.

    Therefore:

        Frame 1 -> Image000001.dat
        Frame 887 -> Image000887.dat
        Frame 894 -> Image000894.dat

    Do NOT add 1 to frame_number.
    """

    frame_number = int(
        frame_number
    )

    candidates = [
        DATASET / f"Image{frame_number:06d}.dat",
        DATASET / f"Image{frame_number:07d}.dat",
    ]

    for candidate in candidates:

        if candidate.exists():
            return candidate

    # Fallback search for unusual zero padding.

    for path in DATASET.glob(
        "*.dat"
    ):

        stem = path.stem

        if not stem.lower().startswith(
            "image"
        ):
            continue

        try:

            number = int(
                stem[5:]
            )

        except ValueError:

            continue

        if number == frame_number:
            return path

    return None


# =============================================================================
# DECODER
# =============================================================================

def convert_to_image_array(decoded):
    """
    Convert the decoder result into a numeric 2-D NumPy array.
    """

    # -------------------------------------------------------------------------
    # NumPy array
    # -------------------------------------------------------------------------

    if isinstance(
        decoded,
        np.ndarray,
    ):

        if decoded.dtype != object:

            array = np.asarray(
                decoded,
                dtype=np.float32,
            )

            if array.ndim >= 2:
                return array

        if decoded.size == 1:

            try:

                return convert_to_image_array(
                    decoded.item()
                )

            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Object attributes
    # -------------------------------------------------------------------------

    for attribute in [
        "image",
        "data",
        "array",
        "pixels",
        "frame",
        "values",
    ]:

        if not hasattr(
            decoded,
            attribute,
        ):
            continue

        try:

            value = getattr(
                decoded,
                attribute,
            )

            array = np.asarray(
                value
            )

            if (
                array.ndim >= 2
                and array.dtype != object
            ):

                return np.asarray(
                    array,
                    dtype=np.float32,
                )

        except Exception:
            continue

    # -------------------------------------------------------------------------
    # Dictionary
    # -------------------------------------------------------------------------

    if isinstance(
        decoded,
        dict,
    ):

        for key in [
            "image",
            "data",
            "array",
            "pixels",
            "frame",
            "values",
        ]:

            if key not in decoded:
                continue

            try:

                array = np.asarray(
                    decoded[key]
                )

                if (
                    array.ndim >= 2
                    and array.dtype != object
                ):

                    return np.asarray(
                        array,
                        dtype=np.float32,
                    )

            except Exception:
                continue

    # -------------------------------------------------------------------------
    # Generic conversion
    # -------------------------------------------------------------------------

    try:

        array = np.asarray(
            decoded
        )

        if (
            array.ndim >= 2
            and array.dtype != object
        ):

            return np.asarray(
                array,
                dtype=np.float32,
            )

    except Exception:
        pass

    raise TypeError(
        "Could not convert decoded frame to a numeric image array.\n\n"
        f"Type: {type(decoded)}\n"
        f"Representation: {repr(decoded)[:1000]}"
    )


def decode_frame(frame_number):
    """
    Decode the exact ImageXXXXXX.dat corresponding to frame_number.
    """

    path = find_frame_file(
        frame_number
    )

    if path is None:

        raise FileNotFoundError(
            f"Could not find .dat file for "
            f"frame {frame_number}"
        )

    decoder = pipeline.decoder

    method_names = [
        "decode",
        "read",
        "load",
        "decode_dat",
        "read_dat",
    ]

    for method_name in method_names:

        method = getattr(
            decoder,
            method_name,
            None,
        )

        if method is None:
            continue

        # ---------------------------------------------------------------------
        # Path object
        # ---------------------------------------------------------------------

        try:

            decoded = method(
                path
            )

            if decoded is not None:

                return (
                    convert_to_image_array(
                        decoded
                    ),
                    path,
                )

        except TypeError:
            pass

        except Exception:
            pass

        # ---------------------------------------------------------------------
        # String path
        # ---------------------------------------------------------------------

        try:

            decoded = method(
                str(path)
            )

            if decoded is not None:

                return (
                    convert_to_image_array(
                        decoded
                    ),
                    path,
                )

        except Exception:
            pass

    available = [
        name
        for name in dir(decoder)
        if not name.startswith("_")
    ]

    raise AttributeError(
        "Could not determine the decoder API.\n\n"
        "Available RPM222XRDecoder attributes/methods:\n"
        + "\n".join(available)
    )


# =============================================================================
# FRAME PROCESSING
# =============================================================================

def process_frame(frame_number):
    """
    Process the exact frame through MPAP.
    """

    frame_number = int(
        frame_number
    )

    path = find_frame_file(
        frame_number
    )

    if path is None:

        raise FileNotFoundError(
            f"Could not find .dat file for "
            f"frame {frame_number}"
        )

    decoded, decoded_path = (
        decode_frame(
            frame_number
        )
    )

    # Process the exact same .dat file.
    result = pipeline.process_file(
        decoded_path,
        frame_number=frame_number,
    )

    return (
        decoded,
        result,
        decoded_path,
    )


# =============================================================================
# FRAME SELECTION
# =============================================================================

def sample_target_frames(
    start_frame,
    end_frame,
):
    """Return target frames to display."""

    start_frame = int(
        start_frame
    )

    end_frame = int(
        end_frame
    )

    frames = list(
        range(
            start_frame,
            end_frame + 1,
        )
    )

    if len(frames) <= MAX_TARGET_FRAMES_TO_DISPLAY:

        return frames

    indices = np.linspace(
        0,
        len(frames) - 1,
        MAX_TARGET_FRAMES_TO_DISPLAY,
        dtype=int,
    )

    return [
        frames[index]
        for index in indices
    ]


def get_context_frames(event):
    """
    Build BEFORE -> TARGET -> AFTER frame sequence.
    """

    start = int(
        event["Start_Frame"]
    )

    end = int(
        event["End_Frame"]
    )

    before = list(
        range(
            max(
                1,
                start - CONTEXT_BEFORE,
            ),
            start,
        )
    )

    target = sample_target_frames(
        start,
        end,
    )

    after = list(
        range(
            end + 1,
            end + CONTEXT_AFTER + 1,
        )
    )

    return (
        before,
        target,
        after,
    )


# =============================================================================
# REPRESENTATIVE EVENT SELECTION
# =============================================================================

def choose_representative_events(
    events
):
    """
    Select representative LOW_POWDER events.
    """

    low_powder = events[
        events["Classification"]
        .astype(str)
        .str.upper()
        == "LOW_POWDER"
    ].copy()

    if low_powder.empty:
        return {}

    low_powder[
        "Duration_Category"
    ] = (
        low_powder[
            "Duration_Frames"
        ]
        .apply(
            duration_category
        )
    )

    if "Context_Type" in low_powder.columns:

        low_powder[
            "Context_Type"
        ] = (
            low_powder[
                "Context_Type"
            ]
            .astype(str)
            .str.upper()
        )

    else:

        low_powder[
            "Context_Type"
        ] = "UNKNOWN"

    selected = {}

    def choose_near_median(
        group,
        count,
    ):

        if group.empty:
            return group

        feature_columns = [
            column
            for column in [
                "Band3",
                "Band4",
                "Band5",
                "Area_mm2",
                "Circularity",
                "Aspect_Ratio",
            ]
            if column in group.columns
        ]

        if not feature_columns:

            return group.head(
                count
            )

        medians = group[
            feature_columns
        ].median()

        distances = []

        for _, row in group.iterrows():

            distance = 0.0

            for column in feature_columns:

                value = row[column]

                if pd.isna(value):
                    continue

                scale = group[
                    column
                ].std()

                if (
                    pd.isna(scale)
                    or scale == 0
                ):

                    scale = 1.0

                distance += (
                    (
                        float(value)
                        - float(
                            medians[column]
                        )
                    )
                    / float(scale)
                ) ** 2

            distances.append(
                math.sqrt(
                    distance
                )
            )

        group = group.copy()

        group[
            "_representative_distance"
        ] = distances

        return (
            group
            .sort_values(
                "_representative_distance"
            )
            .head(
                count
            )
        )

    # -------------------------------------------------------------------------
    # 1 frame
    # -------------------------------------------------------------------------

    group = low_powder[
        low_powder[
            "Duration_Category"
        ]
        == "1_FRAME"
    ]

    chosen = choose_near_median(
        group,
        MAX_EVENTS_PER_CATEGORY,
    )

    if not chosen.empty:
        selected["1_FRAME"] = chosen

    # -------------------------------------------------------------------------
    # 2 frames
    # -------------------------------------------------------------------------

    group = low_powder[
        low_powder[
            "Duration_Category"
        ]
        == "2_FRAMES"
    ]

    chosen = choose_near_median(
        group,
        MAX_EVENTS_PER_CATEGORY,
    )

    if not chosen.empty:
        selected["2_FRAMES"] = chosen

    # -------------------------------------------------------------------------
    # 3–5 frames
    # -------------------------------------------------------------------------

    group = low_powder[
        low_powder[
            "Duration_Category"
        ]
        == "3_5_FRAMES"
    ]

    chosen = choose_near_median(
        group,
        MAX_EVENTS_PER_CATEGORY,
    )

    if not chosen.empty:
        selected["3_5_FRAMES"] = chosen

    # -------------------------------------------------------------------------
    # Sustained
    # -------------------------------------------------------------------------

    group = low_powder[
        low_powder[
            "Duration_Frames"
        ]
        >= 10
    ]

    chosen = choose_near_median(
        group,
        MAX_EVENTS_PER_CATEGORY,
    )

    if not chosen.empty:
        selected["SUSTAINED"] = chosen

    return selected


# =============================================================================
# TEXT
# =============================================================================

def format_feature_text(
    result
):
    """Create compact feature summary."""

    features = result.features
    bands = result.band_counts

    return (
        f"Classification: "
        f"{result.classification.value}\n"
        f"Area: {features.area_px:.0f} px\n"
        f"Area: {features.area_mm2:.3f} mm²\n"
        f"Circularity: "
        f"{features.circularity:.3f}\n"
        f"Aspect ratio: "
        f"{features.aspect_ratio:.3f}\n"
        f"Band 3: {bands.band3:.0f}\n"
        f"Band 4: {bands.band4:.0f}\n"
        f"Band 5: {bands.band5:.0f}"
    )


def classification_reason(
    result
):
    """Explain the current classifier decision."""

    features = result.features
    bands = result.band_counts
    config = pipeline.classifier.config

    classification = (
        result.classification.value
    )

    if classification == "LASER_OFF":

        return (
            "No detected melt-pool area."
        )

    if classification == "HIGH_POWER":

        return (
            f"Band 5 ({bands.band5:.0f}) > "
            f"high-power threshold "
            f"({config.high_power_band5})."
        )

    if classification == "LOW_POWER":

        if (
            bands.band3
            < config.low_power_band3
        ):

            return (
                f"Band 3 ({bands.band3:.0f}) < "
                f"low-power threshold "
                f"({config.low_power_band3})."
            )

        if (
            bands.band3
            < config.good_band3
        ):

            return (
                f"Band 3 ({bands.band3:.0f}) < "
                f"GOOD threshold "
                f"({config.good_band3})."
            )

        if (
            bands.band4
            < config.good_band4
        ):

            return (
                f"Band 4 ({bands.band4:.0f}) < "
                f"GOOD threshold "
                f"({config.good_band4})."
            )

    if classification == "LOW_POWDER":

        return (
            f"Circularity "
            f"({features.circularity:.3f}) < "
            f"LOW_POWDER threshold "
            f"({config.low_powder_circularity:.3f})."
        )

    if classification == "GOOD":

        return (
            f"Band 3 ({bands.band3:.0f}) ≥ "
            f"{config.good_band3}, "
            f"Band 4 ({bands.band4:.0f}) ≥ "
            f"{config.good_band4}, "
            f"circularity "
            f"({features.circularity:.3f}) ≥ "
            f"{config.minimum_circularity:.3f}."
        )

    return (
        "Classifier returned UNKNOWN."
    )


# =============================================================================
# FIGURE
# =============================================================================

def save_event_figure(
    event,
    category,
    before_frames,
    target_frames,
    after_frames,
):
    """Generate and save one event-context figure."""

    all_frames = (
        before_frames
        + target_frames
        + after_frames
    )

    if not all_frames:
        return False

    records = []

    for frame_number in all_frames:

        print(
            f"    Loading frame "
            f"{frame_number}..."
        )

        try:

            (
                decoded,
                result,
                path,
            ) = process_frame(
                frame_number
            )

            records.append(
                {
                    "frame_number": frame_number,
                    "decoded": decoded,
                    "result": result,
                    "path": path,
                }
            )

        except Exception as exc:

            print(
                f"    WARNING: could not process "
                f"frame {frame_number}: {exc}"
            )

    if not records:
        return False

    columns = len(
        records
    )

    figure_width = max(
        14,
        columns * 3.4,
    )

    fig, axes = plt.subplots(
        3,
        columns,
        figsize=(
            figure_width,
            9,
        ),
        squeeze=False,
    )

    event_id = int(
        event["Event_ID"]
    )

    layer = int(
        event["Layer"]
    )

    start = int(
        event["Start_Frame"]
    )

    end = int(
        event["End_Frame"]
    )

    duration = int(
        event["Duration_Frames"]
    )

    context_type = str(
        event.get(
            "Context_Type",
            "UNKNOWN",
        )
    )

    fig.suptitle(
        (
            f"LOW_POWDER Event {event_id} | "
            f"Layer {layer:02d} | "
            f"Frames {start}–{end} | "
            f"{duration} frames | "
            f"{duration / 60.0:.3f} s\n"
            f"Context: {context_type} | "
            f"Category: {category}"
        ),
        fontsize=14,
    )

    before_set = set(
        before_frames
    )

    target_set = set(
        target_frames
    )

    for column, record in enumerate(
        records
    ):

        frame_number = record[
            "frame_number"
        ]

        decoded = record[
            "decoded"
        ]

        result = record[
            "result"
        ]

        path = record[
            "path"
        ]

        # ---------------------------------------------------------------------
        # Thermal image
        # ---------------------------------------------------------------------

        ax_original = axes[
            0
        ][column]

        ax_original.imshow(
            decoded,
            cmap="inferno",
        )

        if frame_number in target_set:

            ax_original.set_title(
                (
                    f"FRAME {frame_number}\n"
                    f"TARGET\n"
                    f"{path.name}"
                ),
                fontsize=8,
            )

        elif frame_number in before_set:

            ax_original.set_title(
                (
                    f"FRAME {frame_number}\n"
                    f"BEFORE\n"
                    f"{path.name}"
                ),
                fontsize=8,
            )

        else:

            ax_original.set_title(
                (
                    f"FRAME {frame_number}\n"
                    f"AFTER\n"
                    f"{path.name}"
                ),
                fontsize=8,
            )

        ax_original.axis(
            "off"
        )

        # ---------------------------------------------------------------------
        # Features
        # ---------------------------------------------------------------------

        ax_features = axes[
            1
        ][column]

        ax_features.axis(
            "off"
        )

        ax_features.text(
            0.02,
            0.98,
            format_feature_text(
                result
            ),
            transform=ax_features.transAxes,
            verticalalignment="top",
            fontsize=8,
            family="monospace",
        )

        # ---------------------------------------------------------------------
        # Classification
        # ---------------------------------------------------------------------

        ax_reason = axes[
            2
        ][column]

        ax_reason.axis(
            "off"
        )

        ax_reason.text(
            0.02,
            0.98,
            (
                f"CLASS:\n"
                f"{result.classification.value}\n\n"
                f"WHY:\n"
                f"{classification_reason(result)}"
            ),
            transform=ax_reason.transAxes,
            verticalalignment="top",
            fontsize=8,
            wrap=True,
        )

    plt.tight_layout(
        rect=[
            0,
            0,
            1,
            0.90,
        ]
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / (
            f"event_{event_id:04d}"
            f"_L{layer:02d}"
            f"_{category}.png"
        )
    )

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    print(
        f"    SAVED: {output_path}"
    )

    return True


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 90)
    print(
        "MPAP — TRANSIENT EVENT CONTEXT INSPECTION"
    )
    print("=" * 90)

    print()

    print(
        f"Dataset: {DATASET}"
    )

    print(
        f"Input:   {INPUT_CSV}"
    )

    print(
        f"Output:  {OUTPUT_DIR}"
    )

    print()

    events = load_event_data()

    print(
        f"Events loaded: {len(events)}"
    )

    low_powder_events = events[
        events["Classification"]
        .astype(str)
        .str.upper()
        == "LOW_POWDER"
    ]

    print(
        f"LOW_POWDER events: "
        f"{len(low_powder_events)}"
    )

    if low_powder_events.empty:

        print()
        print(
            "No LOW_POWDER events found."
        )

        return

    selected = (
        choose_representative_events(
            events
        )
    )

    print()
    print("-" * 90)
    print(
        "SELECTED REPRESENTATIVE EVENTS"
    )
    print("-" * 90)

    for category, group in selected.items():

        print()
        print(category)

        for _, event in group.iterrows():

            event_id = int(
                event["Event_ID"]
            )

            layer = int(
                event["Layer"]
            )

            start = int(
                event["Start_Frame"]
            )

            end = int(
                event["End_Frame"]
            )

            duration = int(
                event["Duration_Frames"]
            )

            context_type = str(
                event.get(
                    "Context_Type",
                    "UNKNOWN",
                )
            )

            print(
                f"  Event {event_id:4d} | "
                f"L{layer:02d} | "
                f"{start:5d}–{end:5d} | "
                f"{duration:3d} frames | "
                f"{duration / 60.0:.3f} s | "
                f"{context_type}"
            )

    print()
    print("-" * 90)
    print(
        "GENERATING VISUAL INSPECTIONS"
    )
    print("-" * 90)

    total_generated = 0

    for category, group in selected.items():

        print()
        print(
            f"[{category}]"
        )

        for _, event in group.iterrows():

            event_id = int(
                event["Event_ID"]
            )

            print(
                f"  Processing Event "
                f"{event_id}..."
            )

            (
                before_frames,
                target_frames,
                after_frames,
            ) = get_context_frames(
                event
            )

            print(
                f"    Before: {before_frames}"
            )

            print(
                f"    Target: {target_frames}"
            )

            print(
                f"    After:  {after_frames}"
            )

            success = save_event_figure(
                event,
                category,
                before_frames,
                target_frames,
                after_frames,
            )

            if success:
                total_generated += 1

    print()
    print("=" * 90)
    print(
        "INSPECTION COMPLETE"
    )
    print("=" * 90)

    print(
        f"Event inspections generated: "
        f"{total_generated}"
    )

    print()
    print(
        f"Output directory:\n"
        f"{OUTPUT_DIR}"
    )

    print()
    print(
        "Frame numbering check:"
    )

    print(
        "  Event frame N -> ImageNNNNNN.dat"
    )

    print(
        "  No +1 offset is applied."
    )

    print()
    print(
        "Next step: inspect the regenerated "
        "event-context images before making "
        "any classifier or persistence changes."
    )


if __name__ == "__main__":
    main()