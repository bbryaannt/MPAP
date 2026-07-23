from pathlib import Path

from models import AnalysisRun
from models import Build
from models import Layer


def make_build(name, layer_count):

    build = Build(
        name=name,
        path=Path(name)
    )

    for i in range(layer_count):

        build.add_layer(
            Layer(index=i)
        )

    return build


def main():

    run = AnalysisRun(

        name="Research Validation",

        description="Testing MPAP object model"

    )

    run.add_build(

        make_build(
            "Build A",
            100
        )
    )

    run.add_build(

        make_build(
            "Build B",
            105
        )
    )

    print(run)

    print()

    print("Build Count:", run.build_count)

    print("Layer Count:", run.layer_count)

    print("Frame Count:", run.frame_count)

    print("Measured Frames:", run.measured_frame_count)


if __name__ == "__main__":
    main()