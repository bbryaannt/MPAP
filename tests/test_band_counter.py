"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Thermal Band Counter Test
===============================================================================
"""

import numpy as np

from config import config
from pipeline.band_counter import ThermalBandCounter


def main():

    counter = ThermalBandCounter(
        config.analysis.band_edges
    )

    # One pixel from each band, plus boundary values.
    image = np.array(
        [
            [
                27000,
                30000,
                32600,
                35000,
                38200,
                41000,
                43800,
                46000,
                49400,
                52000,
                55000,
            ]
        ],
        dtype=np.uint16,
    )

    bands = counter.count(image)

    print("=" * 40)
    print("Thermal Band Counter Test")
    print("=" * 40)
    print()

    print("Band 1:", bands.band1)
    print("Band 2:", bands.band2)
    print("Band 3:", bands.band3)
    print("Band 4:", bands.band4)
    print("Band 5:", bands.band5)
    print("Total: ", bands.total)

    assert bands.band1 == 2
    assert bands.band2 == 2
    assert bands.band3 == 2
    assert bands.band4 == 2
    assert bands.band5 == 3

    assert bands.total == 11

    print()
    print("PASS: All thermal band counts are correct.")


if __name__ == "__main__":
    main()