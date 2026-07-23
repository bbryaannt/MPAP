from models import Thermal


def main():

    thermal = Thermal(
        mean_intensity=38215.7,
        max_intensity=54721,
        threshold=46500,
    )

    print(thermal)

    print()

    print("Temperature Range:", thermal.temperature_range)


if __name__ == "__main__":
    main()