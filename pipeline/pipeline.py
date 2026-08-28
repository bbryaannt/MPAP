"""
===============================================================================
MPAP
Melt Pool Analysis Platform

End-to-End Frame Processing Pipeline
===============================================================================
"""

from dataclasses import dataclass

from pipeline.classifier import (
    MeltPoolClassification,
    MeltPoolClassifier,
)
from pipeline.decoder import RPM222XRDecoder
from pipeline.image_processor import RPM222XRImageProcessor
from pipeline.melt_pool_detector import MeltPoolDetector
from pipeline.melt_pool_features import (
    MeltPoolFeatureExtractor,
    MeltPoolFeatures,
)


@dataclass(frozen=True)
class ProcessedFrame:
    """
    Complete result from processing one RPM222XR frame.
    """

    features: MeltPoolFeatures
    classification: MeltPoolClassification


class MeltPoolPipeline:
    """
    Runs one RPM222XR .dat frame through the complete MPAP pipeline.
    """

    def __init__(
        self,
        pixels_per_mm: float = 40.0,
        peak_fraction: float = 0.85,
    ):
        self.decoder = RPM222XRDecoder()
        self.image_processor = RPM222XRImageProcessor()
        self.detector = MeltPoolDetector()

        self.feature_extractor = MeltPoolFeatureExtractor(
            pixels_per_mm=pixels_per_mm,
        )

        self.classifier = MeltPoolClassifier()

        self.peak_fraction = peak_fraction

    def process_file(
        self,
        path: str,
    ) -> ProcessedFrame:
        """
        Decode and analyze one RPM222XR .dat file.
        """

        decoded = self.decoder.decode(path)

        mask = self.detector.threshold_from_peak(
            decoded,
            peak_fraction=self.peak_fraction,
        )

        features = self.feature_extractor.extract(
            mask,
        )

        classification = self.classifier.classify(
            features,
        )

        return ProcessedFrame(
            features=features,
            classification=classification,
        )