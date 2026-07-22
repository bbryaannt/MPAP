from models.bounding_box import BoundingBox


def main():

    box = BoundingBox(
        x=100,
        y=200,
        width=30,
        height=10,
    )

    print(box)

    print()

    print("Area:", box.area)

    print("Center:", box.center_x, box.center_y)


if __name__ == "__main__":
    main()