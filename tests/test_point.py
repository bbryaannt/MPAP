from models.point import Point


def main():

    p1 = Point(10, 20)
    p2 = Point(13, 24)

    print("Point 1:", p1)
    print("Point 2:", p2)

    print()

    print("Tuple:", p1.to_tuple())

    print()

    print("Distance:", p1.distance_to(p2))


if __name__ == "__main__":
    main()