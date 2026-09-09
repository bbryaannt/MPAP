from pathlib import Path

import cv2
import matplotlib.pyplot as plt

from pipeline.decoder import RPM222XRDecoder
from pipeline.melt_pool_detector import MeltPoolDetector


folder = Path(
    "/Volumes/Army Research Lab/dat Files/test_1_good_images"
)

files = sorted(folder.glob("*.dat"))

decoder = RPM222XRDecoder()
detector = MeltPoolDetector()

for frame_number in range(112, 122):

    path = files[frame_number]

    decoded = decoder.decode(str(path))

    mask = detector.threshold_from_peak(
        decoded,
        peak_fraction=0.85,
    )

    image = decoded.image

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.imshow(image, cmap="gray")
    plt.title(f"Frame {frame_number} - Original")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.imshow(mask, cmap="gray")
    plt.title(f"Frame {frame_number} - Melt Pool Mask")
    plt.axis("off")

    plt.tight_layout()
    plt.show()