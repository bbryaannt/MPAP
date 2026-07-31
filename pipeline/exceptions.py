"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Custom Exceptions
===============================================================================
"""


class DecoderError(Exception):
    """Base class for decoder errors."""


class InvalidHeaderError(DecoderError):
    """The file header is invalid."""


class UnsupportedSchemaError(DecoderError):
    """The schema is not supported."""


class UnsupportedBitDepthError(DecoderError):
    """The bit depth is not supported."""


class CorruptFileError(DecoderError):
    """The file appears to be corrupt or incomplete."""