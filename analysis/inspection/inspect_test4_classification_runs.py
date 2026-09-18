from pathlib import Path
import pandas as pd


DATASET = Path(
    "/Volumes/Army Research Lab/dat Files/test_4_too_low_powder"
)

DIAGNOSTIC_CSV = DATASET / "classification_diagnostic.csv"


def load_data():
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
            f"Missing columns: {sorted(missing)}"
        )

    return df


def reconstruct_layers(df):
    layers = []
    current = []

    for _, row in df.iterrows():
        if row["Classification"] == "LASER_OFF":
            if current:
                layers.append(pd.DataFrame(current).reset_index(drop=True))
                current = []
        else:
            current.append(row)

    if current:
        layers.append(pd.DataFrame(current).reset_index(drop=True))

    return layers


def find_runs(layer_df):
    runs = []

    if layer_df.empty:
        return runs

    start_idx = 0
    current_class = str(
        layer_df.iloc[0]["Classification"]
    )

    for i in range(1, len(layer_df)):
        classification = str(
            layer_df.iloc[i]["Classification"]
        )

        if classification != current_class:
            runs.append(
                (
                    current_class,
                    start_idx,
                    i - 1,
                )
            )

            start_idx = i
            current_class = classification

    runs.append(
        (
            current_class,
            start_idx,
            len(layer_df) - 1,
        )
    )

    return runs


def describe_run(layer_df, classification, start, end):
    run = layer_df.iloc[start:end + 1]

    first_frame = int(run.iloc[0]["Frame"])
    last_frame = int(run.iloc[-1]["Frame"])

    return (
        f"{classification:<11} "
        f"{first_frame:5d}-{last_frame:5d} "
        f"({len(run):3d} frames) "
        f"Area {run['Area_mm2'].mean():6.3f} "
        f"Cir {run['Circularity'].mean():.3f} "
        f"B3 {run['Band3'].mean():7.1f} "
        f"B4 {run['Band4'].mean():6.1f}"
    )


def main():
    df = load_data()
    layers = reconstruct_layers(df)

    print("=" * 100)
    print("TEST 4 FRAME-LEVEL CLASSIFICATION RUNS")
    print("=" * 100)
    print()

    total_transitions = 0

    for layer_number, layer_df in enumerate(
        layers,
        start=1,
    ):
        runs = find_runs(layer_df)

        if len(runs) <= 1:
            continue

        print(
            f"Layer {layer_number} "
            f"({int(layer_df.iloc[0]['Frame'])}-"
            f"{int(layer_df.iloc[-1]['Frame'])})"
        )
        print("-" * 100)

        for classification, start, end in runs:
            print(
                describe_run(
                    layer_df,
                    classification,
                    start,
                    end,
                )
            )

        print()

        total_transitions += len(runs) - 1

    print("=" * 100)
    print(f"TOTAL FRAME-LEVEL CLASSIFICATION TRANSITIONS: {total_transitions}")
    print("=" * 100)


if __name__ == "__main__":
    main()
