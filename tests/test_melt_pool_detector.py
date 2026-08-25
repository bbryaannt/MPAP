"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Detector Test
===============================================================================
"""

import numpy as np

from pipeline.decoder import RPM222XRDecoder
from pipeline.melt_pool_detector import MeltPoolDetector
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
    detector = MeltPoolDetector()

    decoded = decoder.decode(path)

    mask = detector.threshold_from_peak(
        decoded,
        peak_fraction=0.85,
    )

    roi_mask = detector.create_roi_mask(decoded)

    print("=" * 40)
    print("Melt Pool Detector Test")
    print("=" * 40)
    print()

    print("Image:")
    print("  Shape:        ", decoded.shape)
    print("  Data Type:    ", decoded.dtype)
    print("  Min Pixel:    ", decoded.image.min())
    print("  Max Pixel:    ", decoded.image.max())
    print()

    peak = decoded.image.max()
    threshold = int(peak * 0.85)

    print("Detection:")
    print("  Peak Pixel:   ", peak)
    print("  Threshold:    ", threshold)
    print("  Peak Fraction:", 0.85)
    print()

    print("ROI:")
    print("  Shape:        ", roi_mask.shape)
    print("  ROI Pixels:   ", np.count_nonzero(roi_mask))
    print()

    print("Melt Pool Mask:")
    print("  Shape:        ", mask.shape)
    print("  Data Type:    ", mask.dtype)
    print("  Melt Pool Pixels:", np.count_nonzero(mask))
    print("  Background Pixels:", np.count_nonzero(~mask))


if __name__ == "__main__":
    main()