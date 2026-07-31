from pipeline.decoder import RPM222XRDecoder


def main():

    decoder = RPM222XRDecoder()

    print(type(decoder).__name__)

    print()

    print("Decoder successfully created.")


if __name__ == "__main__":
    main()