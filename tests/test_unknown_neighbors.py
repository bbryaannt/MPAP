from pathlib import Path
from collections import Counter

from pipeline.pipeline import MeltPoolPipeline
from pipeline.classifier import MeltPoolClassification


# ======================================================================================================================
# CONFIGURATION
# ======================================================================================================================

DATASET_DIR = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)

ACTIVE_FRAMES_TO_SHOW = 8


# ======================================================================================================================
# DATA PROCESSING
# ======================================================================================================================

def process_dataset():
    files = sorted(DATASET_DIR.glob("*.dat"))

    if not files:
        raise FileNotFoundError(
            f"No .dat files found in:\n{DATASET_DIR}"
        )

    pipeline = MeltPoolPipeline()

    results = []

    print(f"Found {len(files):,} .dat files.")
    print("Processing dataset...")

    for frame_number, path in enumerate(files):
        result = pipeline.process_file(str(path))

        results.append(
            {
                "frame": frame_number,
                "filename": path.name,
                "classification": result.classification,
                "features": result.features,
                "bands": result.band_counts,
            }
        )

    return results


# ======================================================================================================================
# ACTIVE FRAME DETECTION
# ======================================================================================================================

def is_active(result):
    return result["classification"] != MeltPoolClassification.LASER_OFF


def find_active_transitions(results):
    transitions = []

    previous_active = False

    for i, result in enumerate(results):
        active = is_active(result)

        if active and not previous_active:
            transitions.append(i)

        previous_active = active

    return transitions


# ======================================================================================================================
# PRINTING
# ======================================================================================================================

def classification_name(classification):
    if isinstance(classification, MeltPoolClassification):
        return classification.value.upper()

    return str(classification).upper()


def print_transition(results, start_index, transition_number):
    end_index = min(
        start_index + ACTIVE_FRAMES_TO_SHOW,
        len(results)
    )

    print()
    print("-" * 120)
    print(
        f"TRANSITION STARTING AT FRAME {start_index}"
    )
    print("-" * 120)

    print(
        f"{'Frame':>6} | "
        f"{'Rel':>3} | "
        f"{'Filename':<18} | "
        f"{'Class':<10} | "
        f"Metrics"
    )

    print("-" * 120)

    unknown_count = 0

    for i in range(start_index, end_index):
        result = results[i]

        relative_frame = i - start_index

        classification = result["classification"]

        if classification == MeltPoolClassification.UNKNOWN:
            unknown_count += 1

        features = result["features"]
        bands = result["bands"]

        area_mm2 = features.area_mm2
        circularity = features.circularity

        b3 = bands.band3
        b4 = bands.band4
        b5 = bands.band5

        first_active_marker = ""

        if relative_frame == 0:
            first_active_marker = " <-- FIRST ACTIVE"

        print(
            f"{i:6d} | "
            f"+{relative_frame:2d} | "
            f"{result['filename']:<18} | "
            f"{classification_name(classification):<10} | "
            f"Area={area_mm2:6.3f} mm² | "
            f"B3={b3:5d} | "
            f"B4={b4:4d} | "
            f"B5={b5:3d} | "
            f"Circ={circularity:.3f}"
            f"{first_active_marker}"
        )

    print()
    print(
        f"UNKNOWN frames in first "
        f"{end_index - start_index} active frames: "
        f"{unknown_count}"
    )

    return unknown_count


# ======================================================================================================================
# UNKNOWN FRAME SUMMARY
# ======================================================================================================================

def print_unknown_summary(results):
    unknown_frames = [
        result
        for result in results
        if result["classification"] == MeltPoolClassification.UNKNOWN
    ]

    print()
    print("=" * 120)
    print("UNKNOWN FRAME SUMMARY")
    print("=" * 120)

    print(
        f"Total UNKNOWN frames: {len(unknown_frames)}"
    )

    if not unknown_frames:
        print()
        print("No UNKNOWN frames found.")
        return

    print()

    print(
        f"{'Frame':>6} | "
        f"{'Filename':<18} | "
        f"{'Area':>10} | "
        f"{'B3':>6} | "
        f"{'B4':>5} | "
        f"{'B5':>4} | "
        f"{'Circ':>6}"
    )

    print("-" * 80)

    for result in unknown_frames:
        frame = result["frame"]
        filename = result["filename"]
        features = result["features"]
        bands = result["bands"]

        print(
            f"{frame:6d} | "
            f"{filename:<18} | "
            f"{features.area_mm2:10.3f} | "
            f"{bands.band3:6d} | "
            f"{bands.band4:5d} | "
            f"{bands.band5:4d} | "
            f"{features.circularity:6.3f}"
        )


# ======================================================================================================================
# UNKNOWN POSITION ANALYSIS
# ======================================================================================================================

def print_unknown_position_analysis(results, transitions):
    print()
    print("=" * 120)
    print("UNKNOWN POSITION CHECK")
    print("=" * 120)

    unknown_frames = [
        result["frame"]
        for result in results
        if result["classification"] == MeltPoolClassification.UNKNOWN
    ]

    if not unknown_frames:
        print()
        print("Total UNKNOWN frames: 0")
        return

    print()
    print(
        f"Total UNKNOWN frames: {len(unknown_frames)}"
    )

    print()

    position_counts = Counter()

    for unknown_frame in unknown_frames:
        closest_transition = None

        for transition in transitions:
            if transition <= unknown_frame:
                closest_transition = transition
            else:
                break

        if closest_transition is None:
            print(
                f"Frame {unknown_frame}: "
                "UNKNOWN occurred before any detected transition"
            )
            continue

        relative_position = unknown_frame - closest_transition

        position_counts[relative_position] += 1

        print(
            f"Frame {unknown_frame:5d} | "
            f"Transition {closest_transition:5d} | "
            f"Relative position +{relative_position}"
        )

    print()
    print("UNKNOWN POSITION COUNTS")
    print("-" * 60)

    for position in sorted(position_counts):
        print(
            f"+{position}: "
            f"{position_counts[position]} UNKNOWN frame(s)"
        )


# ======================================================================================================================
# TRANSITION SUMMARY
# ======================================================================================================================

def print_transition_summary(
    results,
    transitions,
    transition_unknown_counts
):
    print()
    print("=" * 120)
    print("TRANSITION SUMMARY")
    print("=" * 120)

    print()

    print(
        f"Active transitions: {len(transitions)}"
    )

    total_unknown = sum(
        transition_unknown_counts
    )

    print(
        f"UNKNOWN frames within analyzed transition windows: "
        f"{total_unknown}"
    )

    print()

    print(
        f"{'Transition':>12} | "
        f"{'First Class':<12} | "
        f"{'UNKNOWN Count':>13}"
    )

    print("-" * 60)

    for transition, unknown_count in zip(
        transitions,
        transition_unknown_counts
    ):
        first_class = classification_name(
            results[transition]["classification"]
        )

        print(
            f"{transition:12d} | "
            f"{first_class:<12} | "
            f"{unknown_count:13d}"
        )


# ======================================================================================================================
# CLASSIFICATION COUNTS
# ======================================================================================================================

def print_classification_counts(results):
    counts = Counter(
        classification_name(
            result["classification"]
        )
        for result in results
    )

    print()
    print("=" * 120)
    print("FULL DATASET CLASSIFICATION COUNTS")
    print("=" * 120)

    print()

    for classification, count in sorted(
        counts.items()
    ):
        print(
            f"{classification:<15} : {count:,}"
        )


# ======================================================================================================================
# MAIN
# ======================================================================================================================

def main():
    print("=" * 120)
    print("MPAP LASER-ON TRANSITION DIAGNOSTIC")
    print("=" * 120)

    print()
    print(
        f"Dataset: {DATASET_DIR}"
    )

    print(
        f"Active frames shown per transition: "
        f"{ACTIVE_FRAMES_TO_SHOW}"
    )

    print()
    print(
        "This diagnostic does NOT modify the MPAP pipeline."
    )

    print()

    # --------------------------------------------------------------------------------------------------------------
    # PROCESS DATASET
    # --------------------------------------------------------------------------------------------------------------

    results = process_dataset()

    # --------------------------------------------------------------------------------------------------------------
    # FIND TRANSITIONS
    # --------------------------------------------------------------------------------------------------------------

    transitions = find_active_transitions(results)

    print()
    print()
    print("=" * 120)
    print("LASER-ON TRANSITIONS")
    print("=" * 120)

    print()
    print(
        f"Total active transitions found: "
        f"{len(transitions)}"
    )

    # --------------------------------------------------------------------------------------------------------------
    # PRINT EACH TRANSITION
    # --------------------------------------------------------------------------------------------------------------

    transition_unknown_counts = []

    for transition_number, transition in enumerate(
        transitions,
        start=1
    ):
        unknown_count = print_transition(
            results,
            transition,
            transition_number
        )

        transition_unknown_counts.append(
            unknown_count
        )

    # --------------------------------------------------------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------------------------------------------------------

    print_transition_summary(
        results,
        transitions,
        transition_unknown_counts
    )

    # --------------------------------------------------------------------------------------------------------------
    # UNKNOWN POSITION ANALYSIS
    # --------------------------------------------------------------------------------------------------------------

    print_unknown_position_analysis(
        results,
        transitions
    )

    # --------------------------------------------------------------------------------------------------------------
    # UNKNOWN FRAME DETAILS
    # --------------------------------------------------------------------------------------------------------------

    print_unknown_summary(results)

    # --------------------------------------------------------------------------------------------------------------
    # FULL CLASSIFICATION COUNTS
    # --------------------------------------------------------------------------------------------------------------

    print_classification_counts(results)

    # --------------------------------------------------------------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------------------------------------------------------------

    print()
    print("=" * 120)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 120)


if __name__ == "__main__":
    main()