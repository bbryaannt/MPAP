from pathlib import Path
import pandas as pd


DATASET = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)

DIAGNOSTIC_CSV = DATASET / "classification_diagnostic.csv"


def print_separator():
    print("=" * 80)


def load_diagnostic():
    if not DIAGNOSTIC_CSV.exists():
        raise FileNotFoundError(
            f"Could not find:\n{DIAGNOSTIC_CSV}\n\n"
            "Run the classification analysis for Test 4 first."
        )

    df = pd.read_csv(DIAGNOSTIC_CSV)

    required = {
        "Frame",
        "Classification",
        "Area_mm2",
        "Circularity",
        "Aspect_Ratio",
        "Band3",
        "Band4",
        "Band5",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    return df


def reconstruct_active_layers(df):
    """
    Reconstruct layer numbers from LASER_OFF gaps.

    A layer is treated as a contiguous active section separated
    from the next layer by one or more LASER_OFF frames.
    """

    layers = []
    current_frames = []

    for _, row in df.iterrows():
        classification = str(row["Classification"])

        if classification == "LASER_OFF":
            if current_frames:
                layers.append(current_frames)
                current_frames = []
        else:
            current_frames.append(row)

    if current_frames:
        layers.append(current_frames)

    return layers


def classify_layer(layer_df):
    counts = layer_df["Classification"].value_counts()

    if counts.empty:
        return "UNKNOWN"

    dominant = counts.index[0]
    dominant_percent = (
        counts.iloc[0] / len(layer_df) * 100.0
    )

    if dominant_percent >= 70.0:
        return dominant

    return "TRANSITION"


def layer_summary(layer_df, layer_number):
    status = classify_layer(layer_df)

    return {
        "layer": layer_number,
        "first_frame": int(layer_df["Frame"].iloc[0]),
        "last_frame": int(layer_df["Frame"].iloc[-1]),
        "frames": len(layer_df),
        "status": status,
        "good": int((layer_df["Classification"] == "GOOD").sum()),
        "low_powder": int(
            (layer_df["Classification"] == "LOW_POWDER").sum()
        ),
        "low_power": int(
            (layer_df["Classification"] == "LOW_POWER").sum()
        ),
        "high_power": int(
            (layer_df["Classification"] == "HIGH_POWER").sum()
        ),
        "unknown": int(
            (layer_df["Classification"] == "UNKNOWN").sum()
        ),
        "area_mean": layer_df["Area_mm2"].mean(),
        "circularity_mean": layer_df["Circularity"].mean(),
        "aspect_ratio_mean": layer_df["Aspect_Ratio"].mean(),
        "band3_mean": layer_df["Band3"].mean(),
        "band4_mean": layer_df["Band4"].mean(),
        "band5_mean": layer_df["Band5"].mean(),
    }


def print_layer_summary(summary):
    print(
        f"L{summary['layer']:02d} "
        f"Frames {summary['first_frame']:5d}-{summary['last_frame']:5d} "
        f"({summary['frames']:4d} frames)  "
        f"{summary['status']}"
    )

    print(
        f"    GOOD={summary['good']:4d}  "
        f"LOW_POWDER={summary['low_powder']:4d}  "
        f"LOW_POWER={summary['low_power']:4d}  "
        f"HIGH_POWER={summary['high_power']:4d}  "
        f"UNKNOWN={summary['unknown']:4d}"
    )

    print(
        f"    Area={summary['area_mean']:.4f} mm²  "
        f"Cir={summary['circularity_mean']:.4f}  "
        f"AR={summary['aspect_ratio_mean']:.4f}  "
        f"B3={summary['band3_mean']:.1f}  "
        f"B4={summary['band4_mean']:.1f}  "
        f"B5={summary['band5_mean']:.1f}"
    )


def choose_frame_near_position(layer_df, fraction):
    """
    Select a frame near a fractional position through a layer.
    fraction=0.0 means beginning, 1.0 means end.
    """

    if layer_df.empty:
        return None

    index = int(
        round(
            fraction * (len(layer_df) - 1)
        )
    )

    index = max(0, min(index, len(layer_df) - 1))

    return layer_df.iloc[index]


def print_selected_frame(row, label):
    print(
        f"{label}: "
        f"Frame {int(row['Frame'])} | "
        f"{row['Classification']} | "
        f"Area {row['Area_mm2']:.4f} mm² | "
        f"Cir {row['Circularity']:.4f} | "
        f"AR {row['Aspect_Ratio']:.4f} | "
        f"B3 {row['Band3']:.1f} | "
        f"B4 {row['Band4']:.1f} | "
        f"B5 {row['Band5']:.1f}"
    )


def main():
    df = load_diagnostic()

    layers = reconstruct_active_layers(df)

    print_separator()
    print("TEST 4 PROCESS PROGRESSION")
    print_separator()

    print(f"Dataset: {DATASET}")
    print(f"Total frames: {len(df)}")
    print(f"Detected active layers: {len(layers)}")
    print()

    summaries = []

    for layer_number, layer_rows in enumerate(layers, start=1):
        layer_df = pd.DataFrame(layer_rows).reset_index(drop=True)

        summary = layer_summary(
            layer_df,
            layer_number,
        )

        summaries.append(summary)
        print_layer_summary(summary)

    print()
    print_separator()
    print("KEY LAYER TRANSITIONS")
    print_separator()

    previous_status = None

    for summary in summaries:
        status = summary["status"]

        if status != previous_status:
            print(
                f"Layer {summary['layer']}: "
                f"{previous_status or 'START'} -> {status}"
            )
            previous_status = status

    print()
    print_separator()
    print("REPRESENTATIVE PROGRESSION FRAMES")
    print_separator()

    # Early GOOD region
    if len(layers) >= 1:
        layer_df = pd.DataFrame(layers[0]).reset_index(drop=True)

        print("\nEARLY BUILD:")
        print_selected_frame(
            choose_frame_near_position(layer_df, 0.25),
            "Layer 1 early",
        )
        print_selected_frame(
            choose_frame_near_position(layer_df, 0.75),
            "Layer 1 late",
        )

    # Beginning of LOW_POWDER region
    if len(layers) >= 2:
        layer_df = pd.DataFrame(layers[1]).reset_index(drop=True)

        print("\nBEGINNING OF CHANGE:")
        print_selected_frame(
            choose_frame_near_position(layer_df, 0.10),
            "Layer 2 early",
        )
        print_selected_frame(
            choose_frame_near_position(layer_df, 0.50),
            "Layer 2 middle",
        )
        print_selected_frame(
            choose_frame_near_position(layer_df, 0.90),
            "Layer 2 late",
        )

    # Around transition region
    transition_layers = [
        s["layer"]
        for s in summaries
        if s["status"] == "TRANSITION"
    ]

    if transition_layers:
        print("\nTRANSITION REGION:")

        for layer_number in transition_layers:
            layer_df = pd.DataFrame(
                layers[layer_number - 1]
            ).reset_index(drop=True)

            print_selected_frame(
                choose_frame_near_position(layer_df, 0.10),
                f"Layer {layer_number} early",
            )

            print_selected_frame(
                choose_frame_near_position(layer_df, 0.50),
                f"Layer {layer_number} middle",
            )

            print_selected_frame(
                choose_frame_near_position(layer_df, 0.90),
                f"Layer {layer_number} late",
            )

    # Beginning of sustained LOW_POWER region
    low_power_layers = [
        s["layer"]
        for s in summaries
        if s["status"] == "LOW_POWER"
    ]

    if low_power_layers:
        first_low_power_layer = low_power_layers[0]
        last_low_power_layer = low_power_layers[-1]

        print("\nSUSTAINED LOW_POWER REGION:")

        layer_df = pd.DataFrame(
            layers[first_low_power_layer - 1]
        ).reset_index(drop=True)

        print_selected_frame(
            choose_frame_near_position(layer_df, 0.10),
            f"Layer {first_low_power_layer} early",
        )

        print_selected_frame(
            choose_frame_near_position(layer_df, 0.50),
            f"Layer {first_low_power_layer} middle",
        )

        layer_df = pd.DataFrame(
            layers[last_low_power_layer - 1]
        ).reset_index(drop=True)

        print_selected_frame(
            choose_frame_near_position(layer_df, 0.50),
            f"Layer {last_low_power_layer} middle",
        )

        print_selected_frame(
            choose_frame_near_position(layer_df, 0.90),
            f"Layer {last_low_power_layer} late",
        )

    print()
    print_separator()
    print("DONE")
    print_separator()


if __name__ == "__main__":
    main()
