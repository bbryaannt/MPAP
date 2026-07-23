from pathlib import Path

from enums import Classification
from enums import FrameStatus

from models import (
    BandCounts,
    BoundingBox,
    Frame,
    Geometry,
    Layer,
    Measurement,
    Point,
    Thermal,
)


def make_measurement():

    return Measurement(

        geometry=Geometry(
            area_px=150,
            area_mm2=0.09,
            circularity=0.81,
            aspect_ratio=1.05,
        ),

        thermal=Thermal(
            mean_intensity=39000,
            max_intensity=54500,
            threshold=46500,
        ),

        band_counts=BandCounts(
            10,
            20,
            6000,
            250,
            0,
        ),

        geometry_center=Point(640, 190),

        intensity_center=Point(641, 189),

        bounding_box=BoundingBox(
            620,
            175,
            40,
            30,
        ),

        classification=Classification.GOOD,
    )


def main():

    layer = Layer(index=42)

    for i in range(10):

        layer.add_frame(

            Frame(
                index=i,
                path=Path(f"Frame{i:05}.dat"),
                status=FrameStatus.VALID,
                measurement=make_measurement(),
            )

        )

    print(layer)

    print()

    print("Frame Count:", layer.frame_count)

    print("Measured:", layer.measured_frame_count)

    print("Start:", layer.start_frame)

    print("End:", layer.end_frame)

    print("Duration:", layer.duration)


if __name__ == "__main__":
    main()