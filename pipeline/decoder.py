"""
===============================================================================

MPAP

Melt Pool Analysis Platform

RPM222XR Decoder

===============================================================================
"""

import struct
from pathlib import Path

from models import Header, DecodedImage

from pipeline.constants import (
    SCHEMA_0,
    SCHEMA_1,
    SCHEMA_0_HEADER_SIZE,
    SCHEMA_1_MIN_HEADER_BYTES,
    HEADER_FORMAT,
    SUPPORTED_BIT_DEPTHS,
)

from pipeline.exceptions import (
    CorruptFileError,
    UnsupportedSchemaError,
    UnsupportedBitDepthError,
)

from pipeline.pixel_decoder import RPM222XRPixelDecoder


class RPM222XRDecoder:
    """
    Decoder for RPM222XR thermal .dat files.

    This class is responsible for:
    - Detecting the file schema
    - Reading the file header
    - Extracting raw pixel bytes

    Pixel decoding is handled by RPM222XRPixelDecoder.
    """

    def __init__(self):
        self.pixel_decoder = RPM222XRPixelDecoder()

    def decode(self, path: str | Path) -> DecodedImage:
        """
        Decode an RPM222XR .dat file into a DecodedImage.
        """
        path = Path(path)

        header = self._read_header(path)

        pixel_bytes = self._read_pixel_bytes(
            path,
            header,
        )

        image = self.pixel_decoder.decode(
            pixel_bytes,
            header,
        )

        return DecodedImage(
            image=image,
            header=header,
        )

    def peek_header(self, path: str | Path) -> Header:
        """
        Read only the file header.
        """
        return self._read_header(Path(path))

    def validate(self, path: str | Path) -> bool:
        """
        Validate that a file has a readable header.
        """
        self._read_header(Path(path))
        return True

    def _detect_schema(self, path: Path) -> int:
        """
        Detect whether the file uses Schema 0 or Schema 1.
        """
        with path.open("rb") as file:
            first_two = file.read(2)

        if len(first_two) != 2:
            raise CorruptFileError(
                f"{path.name} is too small to contain a valid RPM222XR file."
            )

        if first_two == b"\x00\x00":
            return SCHEMA_1

        return SCHEMA_0

    def _read_header(self, path: Path) -> Header:
        """
        Read and parse the RPM222XR file header.
        """
        schema = self._detect_schema(path)

        with path.open("rb") as file:

            # ==============================================================
            # Schema 0
            # ==============================================================

            if schema == SCHEMA_0:
                raw_header = file.read(
                    SCHEMA_0_HEADER_SIZE
                )

                if len(raw_header) != SCHEMA_0_HEADER_SIZE:
                    raise CorruptFileError(
                        f"{path.name} has an incomplete Schema 0 header."
                    )

                (
                    height,
                    width,
                    bit_depth,
                    pixel_format,
                ) = struct.unpack(
                    HEADER_FORMAT,
                    raw_header,
                )

                header_size = SCHEMA_0_HEADER_SIZE
                header_length_words = None

            # ==============================================================
            # Schema 1
            # ==============================================================

            elif schema == SCHEMA_1:
                fixed_header = file.read(
                    SCHEMA_1_MIN_HEADER_BYTES
                )

                if len(fixed_header) != SCHEMA_1_MIN_HEADER_BYTES:
                    raise CorruptFileError(
                        f"{path.name} has an incomplete Schema 1 header."
                    )

                (
                    schema_id,
                    header_length_words,
                    aoi_left,
                    aoi_top,
                    aoi_right,
                    aoi_bottom,
                    width,
                    bit_depth,
                    pixel_format,
                ) = struct.unpack(
                    "<9I",
                    fixed_header,
                )

                header_size = header_length_words * 4

                remaining = (
                    header_size
                    - SCHEMA_1_MIN_HEADER_BYTES
                )

                raw_header = (
                    fixed_header
                    + file.read(remaining)
                )

                if len(raw_header) != header_size:
                    raise CorruptFileError(
                        f"{path.name} has an incomplete Schema 1 header."
                    )

                height = aoi_bottom - aoi_top

            else:
                raise UnsupportedSchemaError(
                    f"Unsupported schema: {schema}"
                )

        # ==============================================================
        # Validation
        # ==============================================================

        if bit_depth not in SUPPORTED_BIT_DEPTHS:
            raise UnsupportedBitDepthError(
                f"Unsupported bit depth: {bit_depth}"
            )

        return Header(
            schema=schema,
            width=width,
            height=height,
            bit_depth=bit_depth,
            pixel_format=pixel_format,
            header_size=header_size,
            raw_bytes=raw_header,
            header_length_words=header_length_words,
        )

    def _read_pixel_bytes(
        self,
        path: Path,
        header: Header,
    ) -> bytes:
        """
        Read only the raw pixel bytes from an RPM222XR file.
        """
        with path.open("rb") as file:
            file.seek(header.header_size)
            return file.read()
