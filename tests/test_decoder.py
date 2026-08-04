from pipeline.decoder import RPM222XRDecoder
from mpap_io.dialogs import select_file


def main():

    print("Select an RPM222XR .dat file...\n")

    path = select_file(
        title="Select RPM222XR DAT File",
        filetypes=[("DAT Files", "*.dat")],
    )

    if path is None:
        print("No file selected.")
        return

    decoder = RPM222XRDecoder()

    decoded = decoder.decode(path)

    print("=" * 40)
    print("Decoded Image")
    print("=" * 40)
    print()

    print(decoded)
    print()

    print("Shape:        ", decoded.shape)
    print("Data Type:    ", decoded.dtype)
    print("Schema:       ", decoded.schema)
    print("Bit Depth:    ", decoded.bit_depth)
    print("Width:        ", decoded.width)
    print("Height:       ", decoded.height)
    print("Header Size:  ", decoded.header_size)
    print("Min Pixel:    ", decoded.image.min())
    print("Max Pixel:    ", decoded.image.max())


if __name__ == "__main__":
    main()