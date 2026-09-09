"""
===============================================================================
MPAP
Melt Pool Analysis Platform

RPM222XR Constants Tests
===============================================================================
"""

from pipeline.constants import (
    SCHEMA_0,
    SCHEMA_1,
    SCHEMA_0_HEADER_SIZE,
    SCHEMA_1_MIN_HEADER_BYTES,
    HEADER_FORMAT,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    SUPPORTED_BIT_DEPTHS,
    PIXEL_FORMAT_MONO,
    BYTE_ORDER,
)


def test_schema_constants():
    assert SCHEMA_0 == 0
    assert SCHEMA_1 == 1


def test_schema_0_header_size():
    assert SCHEMA_0_HEADER_SIZE == 8


def test_schema_1_minimum_header_size():
    assert SCHEMA_1_MIN_HEADER_BYTES == 36


def test_header_format():
    assert HEADER_FORMAT == "<HHHH"


def test_default_image_size():
    assert DEFAULT_WIDTH == 1280
    assert DEFAULT_HEIGHT == 380


def test_supported_bit_depths():
    assert SUPPORTED_BIT_DEPTHS == (8, 12)


def test_pixel_format():
    assert PIXEL_FORMAT_MONO == 0


def test_byte_order():
    assert BYTE_ORDER == "little"
