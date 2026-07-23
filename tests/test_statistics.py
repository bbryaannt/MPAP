from models import Statistics


def main():

    stats = Statistics(
        mean=10.2,
        median=10.0,
        standard_deviation=0.85,
        minimum=8.7,
        maximum=12.1,
    )

    print(stats)

    print()

    print("Range:", stats.range)

    print("Variation (%):", stats.variation)


if __name__ == "__main__":
    main()