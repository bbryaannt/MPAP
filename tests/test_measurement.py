from enums import Classification

from models import (
    BandCounts,
    BoundingBox,
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

        classification_reason="Rule-based classifier",
    )

    print(measurement)

    print()

    print("Is Good:", measurement.is_good)

    print()

    print(measurement.to_dict())


if __name__ == "__main__":
    main()