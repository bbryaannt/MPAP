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

    header = decoder.peek_header(path)

    pixel_bytes = decoder._read_pixel_bytes(path, header)

    print("=" * 38)
    print("Pixel Byte Information")
    print("=" * 38)
    print()

    print("Header Size:     ", header.header_size)
    print("Pixel Bytes:     ", len(pixel_bytes))
    print("Pixel Count:     ", header.pixel_count)


if __name__ == "__main__":
    main()