"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Thermal Band Counter
===============================================================================
"""

import numpy as np

from config import config
from models.band_counts import BandCounts


class ThermalBandCounter:
    """
    Counts pixels belonging to each configured thermal band.
    """

    def __init__(
        self,
        band_edges: tuple[int, ...] | None = None,
    ):
        self.band_edges = (
            band_edges
            if band_edges is not None
            else config.analysis.band_edges
        )

        if len(self.band_edges) != 6:
            raise ValueError(
                "Exactly 6 band edges are required."
            )

        if tuple(sorted(self.band_edges)) != self.band_edges:
            raise ValueError(
                "Band edges must be in ascending order."
            )

    def count(
        self,
        image: np.ndarray,
    ) -> BandCounts:
        """
        Count pixels across the five thermal bands.

        Values below the lowest edge are placed into Band 1.
        Values above the highest edge are placed into Band 5.
        """

        if image.ndim != 2:
            raise ValueError(
                "Thermal image must be a 2-D array."
            )

        values = image.astype(np.int64)

        e1, e2, e3, e4, e5, e6 = self.band_edges

        band1 = int(
            np.count_nonzero(values < e2)
        )

        band2 = int(
            np.count_nonzero(
                (values >= e2)
                & (values < e3)
            )
        )

        band3 = int(
            np.count_nonzero(
                (values >= e3)
                & (values < e4)
            )
        )

        band4 = int(
            np.count_nonzero(
                (values >= e4)
                & (values < e5)
            )
        )

        band5 = int(
            np.count_nonzero(values >= e5)
        )

        return BandCounts(
            band1=band1,
            band2=band2,
            band3=band3,
            band4=band4,
            band5=band5,
        )