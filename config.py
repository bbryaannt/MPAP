"""
===============================================================================
MPAP - Melt Pool Analysis Platform

Module:
    config.py

Purpose:
    Central configuration for the Melt Pool Analysis Platform.

Author:
    Bryant Barrio

Version:
    2.0.0-alpha.1
===============================================================================
"""

from dataclasses import dataclass, field
from pathlib import Path


# =============================================================================
# PROJECT
# =============================================================================

@dataclass(frozen=True)
class ProjectConfig:
    """General project settings."""

    name: str = "MPAP"
    version: str = "2.0.0-alpha.1"

    debug: bool = False
    verbose: bool = True


# =============================================================================
# MACHINE
# =============================================================================

@dataclass(frozen=True)
class MachineConfig:
    """RPM222XR machine configuration."""

    machine_name: str = "RPM222XR"

    supported_extension: str = ".dat"

    bits_per_pixel: int = 12

    pixels_per_mm: float = 40.0


# =============================================================================
# DECODER
# =============================================================================

@dataclass(frozen=True)
class DecoderConfig:
    """Raw image decoding configuration."""

    validate_headers: bool = True

    allow_unknown_headers: bool = False


# =============================================================================
# ANALYSIS
# =============================================================================

@dataclass(frozen=True)
class AnalysisConfig:
    """Thermal image analysis settings."""

    low_clip: int = 27000

    high_clip: int = 55000

    peak_fraction: float = 0.85

    min_component_area: int = 25

    roi_half_width: int = 250

    roi_half_height: int = 120


# =============================================================================
# CLASSIFICATION
# =============================================================================

@dataclass(frozen=True)
class ClassificationConfig:
    """Rule-based classifier thresholds."""

    high_power_band5: int = 400

    low_power_band3: int = 1000

    good_band3: int = 6000

    good_band4: int = 200

    minimum_circularity: float = 0.74


# =============================================================================
# LAYER DETECTION
# =============================================================================

@dataclass(frozen=True)
class LayerDetectionConfig:
    """Layer detection settings."""

    algorithm: str = "AdaptiveLaserOff"

    minimum_laser_off_frames: int = 240

    minimum_layer_frames: int = 100


# =============================================================================
# VISUALIZATION
# =============================================================================

@dataclass(frozen=True)
class VisualizationConfig:
    """Dashboard configuration."""

    show_layer_lines: bool = True

    show_layer_labels: bool = True

    default_metric: str = "Area_mm2"

    theme: str = "light"


# =============================================================================
# OUTPUT
# =============================================================================

@dataclass(frozen=True)
class OutputConfig:
    """Output file settings."""

    save_csv: bool = True

    save_dashboard: bool = True

    save_logs: bool = True

    output_folder: str = "output"


# =============================================================================
# MASTER CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class MPAPConfig:
    """Master configuration object."""

    project: ProjectConfig = field(default_factory=ProjectConfig)

    machine: MachineConfig = field(default_factory=MachineConfig)

    decoder: DecoderConfig = field(default_factory=DecoderConfig)

    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)

    classification: ClassificationConfig = field(default_factory=ClassificationConfig)

    layer_detection: LayerDetectionConfig = field(default_factory=LayerDetectionConfig)

    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)

    output: OutputConfig = field(default_factory=OutputConfig)


# =============================================================================
# GLOBAL CONFIGURATION INSTANCE
# =============================================================================

config = MPAPConfig()