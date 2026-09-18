from pathlib import Path

from enums.frame_status import FrameStatus
from models import Frame
from monitoring import BuildStateManager


def make_frame(index=1):
    return Frame(
        index=index,
        path=Path(f"frame_{index:04d}.dat"),
        status=FrameStatus.VALID,
    )


def test_build_state_manager_adds_frame():
    manager = BuildStateManager()

    frame = make_frame()

    manager.add_frame(frame)

    assert manager.current_frame == 1
    assert manager.current_layer_number == 1
    assert manager.frames_processed == 1
    assert manager.is_active is True
    assert manager.machine_status == "PROCESSING"
    assert manager.current_layer is not None
    assert manager.current_layer.frame_count == 1


def test_build_state_manager_starts_new_layer():
    manager = BuildStateManager()

    manager.add_frame(make_frame())

    manager.start_new_layer()

    assert manager.current_layer_number == 2
    assert manager.layers_completed == 1
    assert manager.state.total_layers == 2
    assert manager.current_layer.frame_count == 0


def test_build_state_manager_reset():
    manager = BuildStateManager()

    manager.add_frame(make_frame())

    manager.reset()

    assert manager.current_frame == 0
    assert manager.current_layer_number == 0
    assert manager.frames_processed == 0
    assert manager.layers_completed == 0
    assert manager.is_active is False
    assert manager.machine_status == "IDLE"
    assert manager.current_layer is None