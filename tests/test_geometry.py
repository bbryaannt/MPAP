from models import Geometry


def main():

    geometry = Geometry(
        area_px=125.0,
        area_mm2=0.081,
        circularity=0.82,
        aspect_ratio=1.12,
    )

    print(geometry)

    print()

    print("Circular:", geometry.is_circular)


if __name__ == "__main__":
    main()