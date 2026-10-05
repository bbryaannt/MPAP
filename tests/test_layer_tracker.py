import pytest

from monitoring import LayerTracker
from pipeline.classifier import MeltPoolClassification


def test_layer_tracker_requires_positive_threshold():
    with pytest.raises(ValueError):
        LayerTracker(laser_off_threshold=0)


def test_layer_tracker_ignores_initial_laser_off_frames():
    tracker = LayerTracker(laser_off_threshold=3)

    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False

    assert tracker.laser_off_count == 0
    assert tracker.layer_complete is False
    assert tracker.has_seen_active_frame is False


def test_layer_tracker_starts_tracking_after_active_frame():
    tracker = LayerTracker(laser_off_threshold=3)

    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)

    assert tracker.update(MeltPoolClassification.GOOD) is False

    assert tracker.has_seen_active_frame is True
    assert tracker.laser_off_count == 0
    assert tracker.layer_complete is False


def test_layer_tracker_does_not_complete_before_threshold():
    tracker = LayerTracker(laser_off_threshold=3)

    tracker.update(MeltPoolClassification.GOOD)

    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False

    assert tracker.laser_off_count == 2
    assert tracker.layer_complete is False


def test_layer_tracker_marks_layer_complete_at_threshold():
    tracker = LayerTracker(laser_off_threshold=3)

    tracker.update(MeltPoolClassification.GOOD)

    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False

    assert tracker.laser_off_count == 3
    assert tracker.layer_complete is True


def test_layer_tracker_confirms_transition_on_next_active_frame():
    tracker = LayerTracker(laser_off_threshold=3)

    tracker.update(MeltPoolClassification.GOOD)

    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)

    assert tracker.layer_complete is True

    assert tracker.update(MeltPoolClassification.GOOD) is True

    assert tracker.laser_off_count == 0
    assert tracker.layer_complete is False
    assert tracker.has_seen_active_frame is True


def test_layer_tracker_does_not_create_transition_from_trailing_laser_off():
    tracker = LayerTracker(laser_off_threshold=3)

    tracker.update(MeltPoolClassification.GOOD)

    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)

    assert tracker.layer_complete is True
    assert tracker.laser_off_count == 5

    # Build ends while the laser remains off.
    # There is no next active frame, so no new layer is created.
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.layer_complete is True


def test_layer_tracker_only_reports_transition_once():
    tracker = LayerTracker(laser_off_threshold=3)

    tracker.update(MeltPoolClassification.GOOD)

    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)

    assert tracker.update(MeltPoolClassification.GOOD) is True

    # Additional active frames belong to the same layer.
    assert tracker.update(MeltPoolClassification.GOOD) is False
    assert tracker.update(MeltPoolClassification.GOOD) is False


def test_layer_tracker_short_laser_off_does_not_create_transition():
    tracker = LayerTracker(laser_off_threshold=3)

    tracker.update(MeltPoolClassification.GOOD)

    tracker.update(MeltPoolClassification.LASER_OFF)
    tracker.update(MeltPoolClassification.LASER_OFF)

    assert tracker.update(MeltPoolClassification.GOOD) is False

    assert tracker.laser_off_count == 0
    assert tracker.layer_complete is False


def test_layer_tracker_handles_multiple_layers():
    tracker = LayerTracker(laser_off_threshold=2)

    # Layer 1
    assert tracker.update(MeltPoolClassification.GOOD) is False

    # Inter-layer gap
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False

    # First frame of Layer 2
    assert tracker.update(MeltPoolClassification.GOOD) is True

    # Still Layer 2
    assert tracker.update(MeltPoolClassification.GOOD) is False

    # Inter-layer gap
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False

    # First frame of Layer 3
    assert tracker.update(MeltPoolClassification.GOOD) is True


def test_layer_tracker_reset_returns_to_initial_state():
    tracker = LayerTracker(laser_off_threshold=2)

    tracker.update(MeltPoolClassification.GOOD)
    tracker.update(MeltPoolClassification.LASER_OFF)

    assert tracker.has_seen_active_frame is True
    assert tracker.laser_off_count == 1

    tracker.reset()

    assert tracker.has_seen_active_frame is False
    assert tracker.laser_off_count == 0
    assert tracker.layer_complete is False

    # Initial LASER_OFF frames should again be ignored.
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False
    assert tracker.update(MeltPoolClassification.LASER_OFF) is False

    assert tracker.layer_complete is False