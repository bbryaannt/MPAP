from pathlib import Path

from enums import Classification
from enums import FrameStatus

from models import (
    BandCounts,
    BoundingBox,
    Frame,
    Geometry,
    Measurement,
    Point,
    Thermal,
)


def main():

    measurement = Measurement(

        geometry=Geometry(
            area_px=142,
            area_mm2=0.089,
            circularity=0.82,
            aspect_ratio=1.08,
        ),

        thermal=Thermal(
            mean_intensity=39210,
            max_intensity=54820,
            threshold=46700,
        ),

        band_counts=BandCounts(
            10,
            25,
            6300,
            220,
            0,
        ),

        geometry_center=Point(
            642.1,
            189.7,
        ),

        intensity_center=Point(
            642.4,
            189.2,
        ),

        bounding_box=BoundingBox(
            620,
            175,
            44,
            28,
        ),

        classification=Classification.GOOD,
    )

    frame = Frame(

        index=152,

        path=Path("Frame00152.dat"),

        status=FrameStatus.VALID,

        measurement=measurement,
    )

    print(frame)

    print()

    print("Filename:", frame.filename)

    print("Stem:", frame.stem)

    print("Has Measurement:", frame.has_measurement)
    

if __name__ == "__main__":
    main()