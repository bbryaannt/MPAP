from models import BoundingBox


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
    print("Center:", box.center)
    print("Left:", box.left)
    print("Right:", box.right)
    print("Top:", box.top)
    print("Bottom:", box.bottom)


if __name__ == "__main__":
    main()