from pathlib import Path

from models import Build
from models import Layer


def main():

    build = Build(
        name="Good Build",
        path=Path("ExampleBuild")
    )

    for i in range(5):

        build.add_layer(
            Layer(index=i)
        )

    print(build)

    print()

    print("Layer Count:", build.layer_count)

    print("Frame Count:", build.frame_count)

    print("Measured Frames:", build.measured_frame_count)

    first = build.first_layer
    last = build.last_layer

    assert first is not None
    assert last is not None

    print("First Layer:", first.index)

    print("Last Layer:", last.index)


if __name__ == "__main__":
    main()