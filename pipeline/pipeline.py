"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Main Melt Pool Analysis Pipeline
===============================================================================
"""

from pathlib import Path
from typing import Optional

import numpy as np

from pipeline.decoder import RPM222XRDecoder
from pipeline.melt_pool_detector import MeltPoolDetector
from pipeline.melt_pool_features import MeltPoolFeatureExtractor
from pipeline.band_counter import ThermalBandCounter
from pipeline.classifier import (
    MeltPoolClassifier,
    MeltPoolClassification,
)

from models import MeltPoolResult


class MeltPoolPipeline:
    """
    End-to-end processing pipeline for a single RPM222XR frame.
    """

    def __init__(
        self,
        pixels_per_mm: float = 40.0,
        peak_fraction: float = 0.85,
        decoder: Optional[RPM222XRDecoder] = None,
        detector: Optional[MeltPoolDetector] = None,
        feature_extractor: Optional[MeltPoolFeatureExtractor] = None,
        band_counter: Optional[ThermalBandCounter] = None,
        classifier: Optional[MeltPoolClassifier] = None,
    ):
        if pixels_per_mm <= 0:
            raise ValueError(
                "pixels_per_mm must be greater than 0."
            )

        if not 0 < peak_fraction <= 1:
            raise ValueError(
                "peak_fraction must be greater than 0 and at most 1."
            )

        self.pixels_per_mm = pixels_per_mm
        self.peak_fraction = peak_fraction

        self.decoder = (
            decoder
            if decoder is not None
            else RPM222XRDecoder()
        )

        self.detector = (
            detector
            if detector is not None
            else MeltPoolDetector()
        )

        self.feature_extractor = (
            feature_extractor
            if feature_extractor is not None
            else MeltPoolFeatureExtractor(
                pixels_per_mm=pixels_per_mm
            )
        )

        self.band_counter = (
            band_counter
            if band_counter is not None
            else ThermalBandCounter()
        )

        self.classifier = (
            classifier
            if classifier is not None
            else MeltPoolClassifier()
        )

    def process_file(
        self,
        file_path: str | Path,
        frame_number: int = 0,
    ) -> MeltPoolResult:

        file_path = Path(file_path)

        decoded = self.decoder.decode(
            str(file_path)
        )

        return self.process_decoded(
            decoded,
            frame_number=frame_number,
            file_path=file_path,
        )

    def process_decoded(
        self,
        decoded,
        frame_number: int = 0,
        file_path: Optional[Path] = None,
    ) -> MeltPoolResult:

        # ---------------------------------------------------------------
        # Step 1: Detect melt-pool mask
        # ---------------------------------------------------------------

        mask = self.detector.threshold_from_peak(
            decoded,
            peak_fraction=self.peak_fraction,
        )

        # ---------------------------------------------------------------
        # Step 2: Count thermal bands
        # ---------------------------------------------------------------

        bands = self.band_counter.count(
            decoded.image
        )

        # ---------------------------------------------------------------
        # Step 3: Laser-off handling
        # ---------------------------------------------------------------

        if not np.any(mask):

            features = self.feature_extractor.extract(
                np.zeros_like(mask, dtype=bool)
            )

            classification = (
                MeltPoolClassification.LASER_OFF
            )

            return MeltPoolResult(
                frame_number=frame_number,
                features=features,
                band_counts=bands,
                classification=classification,
            )

        # ---------------------------------------------------------------
        # Step 4: Extract melt-pool features
        # ---------------------------------------------------------------

        features = self.feature_extractor.extract(
            mask
        )

        # ---------------------------------------------------------------
        # Step 5: Classify
        # ---------------------------------------------------------------

        classification = self.classifier.classify(
            features,
            bands,
        )

        # ---------------------------------------------------------------
        # Step 6: Return result
        # ---------------------------------------------------------------

        return MeltPoolResult(
            frame_number=frame_number,
            features=features,
            band_counts=bands,
            classification=classification,
        )