from pathlib import Path

from models import MeltPoolResult
from monitoring import LayerTracker, LiveBuildMonitor
from pipeline.classifier import MeltPoolClassification


class FakePipeline:
    def __init__(self, classifications=None):
        self.classifications = (
            classifications
            if classifications is not None
            else [MeltPoolClassification.GOOD]
        )
        self._index = 0

    def process_file(self, file_path, frame_number=0):
        classification = self.classifications[
            self._index % len(self.classifications)
        ]
        self._index += 1

        return MeltPoolResult(
            frame_number=frame_number,
            features=type(
                "FakeFeatures",
                (),
                {"area_px": 100.0},
            )(),
            band_counts=type(
                "FakeBands",
                (),
                {
                    "band1": 0,
                    "band2": 0,
                    "band3": 6000,
                    "band4": 200,
                    "band5": 0,
                },
            )(),
            classification=classification,
        )


def create_dat_file(directory: Path, filename: str) -> Path:
    path = directory / filename
    path.write_bytes(b"fake dat data")
    return path


def test_live_build_monitor_processes_new_files(tmp_path):
    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=FakePipeline(),
        stable_checks=1,
    )

    create_dat_file(tmp_path, "Image000001.dat")
    create_dat_file(tmp_path, "Image000002.dat")

    results = monitor.scan_once()

    assert len(results) == 2
    assert monitor.frames_processed == 2
    assert results[0].frame_number == 1
    assert results[1].frame_number == 2
    assert monitor.current_frame == 2
    assert monitor.current_layer_number == 1


def test_live_build_monitor_updates_build_state(tmp_path):
    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=FakePipeline(),
        stable_checks=1,
    )

    create_dat_file(tmp_path, "Image000001.dat")

    monitor.scan_once()

    state = monitor.state_manager.get_state()

    assert state.current_frame == 1
    assert state.frames_processed == 1
    assert state.current_layer == 1
    assert state.is_active is True
    assert state.machine_status == "PROCESSING"
    assert state.last_frame is not None
    assert state.last_frame.index == 1
    assert state.last_frame.status.value == "VALID"


def test_live_build_monitor_does_not_process_same_file_twice(tmp_path):
    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=FakePipeline(),
        stable_checks=1,
    )

    create_dat_file(tmp_path, "Image000001.dat")

    first_scan = monitor.scan_once()
    second_scan = monitor.scan_once()

    assert len(first_scan) == 1
    assert second_scan == []
    assert monitor.frames_processed == 1


def test_live_build_monitor_tracks_classifications(tmp_path):
    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=FakePipeline(),
        stable_checks=1,
    )

    create_dat_file(tmp_path, "Image000001.dat")
    create_dat_file(tmp_path, "Image000002.dat")

    monitor.scan_once()

    summary = monitor.classification_summary

    assert sum(summary.values()) == 2
    assert summary["GOOD"] == 2


def test_live_build_monitor_tracks_latest_result(tmp_path):
    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=FakePipeline(),
        stable_checks=1,
    )

    create_dat_file(tmp_path, "Image000001.dat")

    monitor.scan_once()

    latest = monitor.latest_result

    assert latest is not None
    assert latest.frame_number == 1


def test_live_build_monitor_reset(tmp_path):
    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=FakePipeline(),
        stable_checks=1,
    )

    create_dat_file(tmp_path, "Image000001.dat")

    monitor.scan_once()

    assert monitor.frames_processed == 1
    assert monitor.current_frame == 1

    monitor.reset()

    assert monitor.frames_processed == 0
    assert monitor.current_frame == 0
    assert monitor.current_layer_number == 0
    assert monitor.latest_result is None
    assert monitor.machine_status == "IDLE"

    results = monitor.scan_once()

    assert len(results) == 1
    assert monitor.frames_processed == 1
    assert monitor.current_frame == 1


def test_live_build_monitor_detects_layer_transition_on_next_active_frame(
    tmp_path,
):
    tracker = LayerTracker(laser_off_threshold=3)

    pipeline = FakePipeline(
        classifications=[
            MeltPoolClassification.GOOD,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.GOOD,
        ]
    )

    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=pipeline,
        layer_tracker=tracker,
        stable_checks=1,
    )

    for index in range(1, 6):
        create_dat_file(
            tmp_path,
            f"Image{index:06d}.dat",
        )

    results = monitor.scan_once()

    assert len(results) == 5
    assert monitor.frames_processed == 5
    assert monitor.current_layer_number == 2
    assert monitor.layers_completed == 1

    assert monitor.current_layer is not None
    assert monitor.current_layer.frame_count == 1
    assert monitor.current_layer.frames[0].index == 5

    assert monitor.state_manager.state.layers[0].frame_count == 4


def test_live_build_monitor_does_not_create_layer_from_trailing_off(
    tmp_path,
):
    tracker = LayerTracker(laser_off_threshold=3)

    pipeline = FakePipeline(
        classifications=[
            MeltPoolClassification.GOOD,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.LASER_OFF,
        ]
    )

    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=pipeline,
        layer_tracker=tracker,
        stable_checks=1,
    )

    for index in range(1, 5):
        create_dat_file(
            tmp_path,
            f"Image{index:06d}.dat",
        )

    monitor.scan_once()

    assert monitor.current_layer_number == 1
    assert monitor.layers_completed == 0

    assert monitor.current_layer is not None
    assert monitor.current_layer.frame_count == 4


def test_live_build_monitor_does_not_transition_without_threshold(
    tmp_path,
):
    tracker = LayerTracker(laser_off_threshold=3)

    pipeline = FakePipeline(
        classifications=[
            MeltPoolClassification.GOOD,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.GOOD,
        ]
    )

    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=pipeline,
        layer_tracker=tracker,
        stable_checks=1,
    )

    for index in range(1, 5):
        create_dat_file(
            tmp_path,
            f"Image{index:06d}.dat",
        )

    monitor.scan_once()

    assert monitor.current_layer_number == 1
    assert monitor.layers_completed == 0

    assert monitor.current_layer is not None
    assert monitor.current_layer.frame_count == 4


def test_live_build_monitor_resets_layer_tracker(tmp_path):
    tracker = LayerTracker(laser_off_threshold=2)

    pipeline = FakePipeline(
        classifications=[
            MeltPoolClassification.GOOD,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.LASER_OFF,
            MeltPoolClassification.GOOD,
        ]
    )

    monitor = LiveBuildMonitor(
        tmp_path,
        pipeline=pipeline,
        layer_tracker=tracker,
        stable_checks=1,
    )

    for index in range(1, 5):
        create_dat_file(
            tmp_path,
            f"Image{index:06d}.dat",
        )

    monitor.scan_once()

    assert monitor.current_layer_number == 2

    monitor.reset()

    assert tracker.laser_off_count == 0
    assert tracker.layer_complete is False
    assert tracker.has_seen_active_frame is False