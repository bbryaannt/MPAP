from models import BandCounts


def main():

    bands = BandCounts(
        band1=10,
        band2=20,
        band3=30,
        band4=40,
        band5=50,
    )

    print(bands)

    print()

    print("Band 3:", bands[3])

    print("Total:", bands.total)

    print("As List:", bands.as_list())


if __name__ == "__main__":
    main()