"""
===============================================================================
MPAP
Melt Pool Analysis Platform

RPM222XR Pixel Decoder Test
===============================================================================
"""

from pipeline.pixel_decoder import RPM222XRPixelDecoder
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
    pixel_decoder = RPM222XRPixelDecoder()

    header = decoder.peek_header(path)

    pixel_bytes = decoder._read_pixel_bytes(
        path,
        header,
    )

    image = pixel_decoder.decode(
        pixel_bytes,
        header,
    )

    print("=" * 40)
    print("Pixel Decoder Test")
    print("=" * 40)
    print()

    print("Shape:        ", image.shape)
    print("Data Type:    ", image.dtype)
    print("Width:        ", header.width)
    print("Height:       ", header.height)
    print("Bit Depth:    ", header.bit_depth)
    print("Min Pixel:    ", image.min())
    print("Max Pixel:    ", image.max())


if __name__ == "__main__":
    main()