"""
===============================================================================
MPAP
Melt Pool Analysis Platform

RPM222XR Pixel Decoder
===============================================================================
"""

import numpy as np

from models import Header


class RPM222XRPixelDecoder:
    """
    Decodes raw RPM222XR pixel bytes into a NumPy image array.
    """

    def decode(
        self,
        pixel_bytes: bytes,
        header: Header,
    ) -> np.ndarray:
        """
        Decode raw pixel bytes according to the image bit depth.
        """

        if header.bit_depth == 8:
            return self._decode_8bit(
                pixel_bytes,
                header,
            )

        if header.bit_depth == 12:
            return self._decode_12bit(
                pixel_bytes,
                header,
            )

        raise ValueError(
            f"Unsupported bit depth: {header.bit_depth}"
        )

    def _decode_8bit(
        self,
        pixel_bytes: bytes,
        header: Header,
    ) -> np.ndarray:
        """
        Decode 8-bit RPM222XR image data.
        """

        image = np.frombuffer(
            pixel_bytes,
            dtype=np.uint8,
        )

        image = image[:header.pixel_count]

        image = image.reshape(
            (
                header.height,
                header.width,
            )
        )

        return image.astype(np.uint16) * 257

    def _decode_12bit(
        self,
        pixel_bytes: bytes,
        header: Header,
    ) -> np.ndarray:
        """
        Decode 12-bit packed RPM222XR image data.
        """

        raw = np.frombuffer(
            pixel_bytes,
            dtype=np.uint8,
        )

        usable_bytes = (len(raw) // 3) * 3

        raw = raw[:usable_bytes]

        triples = raw.reshape(
            (-1, 3)
        )

        b0 = triples[:, 0].astype(np.uint16)
        b1 = triples[:, 1].astype(np.uint16)
        b2 = triples[:, 2].astype(np.uint16)

        p1 = (b0 << 4) | (b1 & 0x0F)
        p2 = (b2 << 4) | ((b1 >> 4) & 0x0F)

        decoded = np.empty(
            p1.size * 2,
            dtype=np.uint16,
        )

        decoded[0::2] = p1
        decoded[1::2] = p2

        decoded = decoded[:header.pixel_count]

        image = decoded.reshape(
            (
                header.height,
                header.width,
            )
        )

        return (
            image.astype(np.uint32) * 16
        ).astype(np.uint16)