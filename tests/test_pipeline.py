"""
===============================================================================
MPAP
Melt Pool Analysis Platform

End-to-End Pipeline Test
===============================================================================
"""

from pipeline.pipeline import MeltPoolPipeline
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

    pipeline = MeltPoolPipeline(
        pixels_per_mm=40.0,
        peak_fraction=0.85,
    )

    result = pipeline.process_file(path)

    features = result.features
    classification = result.classification

    print("=" * 40)
    print("End-to-End Pipeline Test")
    print("=" * 40)
    print()

    print("Classification:")
    print("  ", classification.value)
    print()

    print("Features:")
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