"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Melt Pool Feature Extraction Test
===============================================================================
"""

from pipeline.decoder import RPM222XRDecoder
from pipeline.melt_pool_detector import MeltPoolDetector
from pipeline.melt_pool_features import MeltPoolFeatureExtractor
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
    extractor = MeltPoolFeatureExtractor(
        pixels_per_mm=40.0,
    )

    decoded = decoder.decode(path)

    mask = detector.threshold_from_peak(
        decoded,
        peak_fraction=0.85,
    )

    features = extractor.extract(mask)

    print("=" * 40)
    print("Melt Pool Feature Extraction Test")
    print("=" * 40)
    print()

    print("Melt Pool Features:")
    print("  Area (px):       ", features.area_px)
    print("  Area (mm²):      ", features.area_mm2)
    print("  Centroid X:      ", features.centroid_x)
    print("  Centroid Y:      ", features.centroid_y)
    print("  BBox Width:      ", features.bbox_width)
    print("  BBox Height:     ", features.bbox_height)
    print("  Aspect Ratio:    ", features.aspect_ratio)
    print("  Circularity:     ", features.circularity)


if __name__ == "__main__":
    main()