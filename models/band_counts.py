"""
===============================================================================
MPAP

Band Counts Model

Stores the number of pixels within each thermal band.
===============================================================================
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BandCounts:
    """
    Stores the number of pixels belonging to each thermal band.
    """

    band1: int
    band2: int
    band3: int
    band4: int
    band5: int

    @property
    def total(self) -> int:
        """Return the total number of pixels across all bands."""
        return (
            self.band1
            + self.band2
            + self.band3
            + self.band4
            + self.band5
        )

    def __getitem__(self, band: int) -> int:
        """
        Allow indexing by band number (1–5).

        Example:
            bands[3]
        """
        mapping = {
            1: self.band1,
            2: self.band2,
            3: self.band3,
            4: self.band4,
            5: self.band5,
        }

        if band not in mapping:
            raise IndexError("Band index must be between 1 and 5.")

        return mapping[band]

    def as_list(self) -> list[int]:
        """Return the band counts as a list."""
        return [
            self.band1,
            self.band2,
            self.band3,
            self.band4,
            self.band5,
        ]
