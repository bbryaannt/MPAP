"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Image Processor Test
===============================================================================
"""

import numpy as np

from pipeline.decoder import RPM222XRDecoder
from pipeline.image_processor import RPM222XRImageProcessor
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
    processor = RPM222XRImageProcessor()

    decoded = decoder.decode(path)

    normalized = processor.normalize(decoded)

    clipped = processor.clip(
        decoded,
        low=27000,
        high=55000,
    )

    thresholded = processor.threshold(
        decoded,
        value=40000,
    )

    print("=" * 40)
    print("Image Processor Test")
    print("=" * 40)
    print()

    print("Original:")
    print("  Shape:        ", decoded.shape)
    print("  Data Type:    ", decoded.dtype)
    print("  Min Pixel:    ", decoded.image.min())
    print("  Max Pixel:    ", decoded.image.max())
    print()

    print("Normalized:")
    print("  Shape:        ", normalized.shape)
    print("  Data Type:    ", normalized.dtype)
    print("  Min Value:    ", normalized.min())
    print("  Max Value:    ", normalized.max())
    print()

    print("Clipped:")
    print("  Shape:        ", clipped.shape)
    print("  Data Type:    ", clipped.dtype)
    print("  Min Value:    ", clipped.min())
    print("  Max Value:    ", clipped.max())
    print()

    print("Threshold:")
    print("  Shape:        ", thresholded.shape)
    print("  Data Type:    ", thresholded.dtype)
    print("  True Pixels:  ", np.count_nonzero(thresholded))
    print("  False Pixels: ", np.count_nonzero(~thresholded))


if __name__ == "__main__":
    main()