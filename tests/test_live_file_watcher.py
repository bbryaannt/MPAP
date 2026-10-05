from pathlib import Path

import pytest

from monitoring import LiveFileWatcher


def test_live_file_watcher_detects_new_dat_file(tmp_path):
    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
    )

    frame = tmp_path / "Image000001.dat"
    frame.write_bytes(b"test data")

    detected = watcher.scan()

    assert detected == [frame]


def test_live_file_watcher_does_not_return_same_file_twice(tmp_path):
    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
    )

    frame = tmp_path / "Image000001.dat"
    frame.write_bytes(b"test data")

    first_scan = watcher.scan()
    second_scan = watcher.scan()

    assert first_scan == [frame]
    assert second_scan == []


def test_live_file_watcher_ignores_non_dat_files(tmp_path):
    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
    )

    dat_file = tmp_path / "Image000001.dat"
    txt_file = tmp_path / "notes.txt"

    dat_file.write_bytes(b"dat")
    txt_file.write_text("ignore me")

    detected = watcher.scan()

    assert detected == [dat_file]


def test_live_file_watcher_mark_seen(tmp_path):
    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
    )

    frame = tmp_path / "Image000001.dat"
    frame.write_bytes(b"test data")

    watcher.mark_seen(frame)

    assert watcher.scan() == []


def test_live_file_watcher_reset(tmp_path):
    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
    )

    frame = tmp_path / "Image000001.dat"
    frame.write_bytes(b"test data")

    assert watcher.scan() == [frame]

    watcher.reset()

    assert watcher.scan() == [frame]


def test_live_file_watcher_requires_existing_directory(tmp_path):
    missing = tmp_path / "missing"

    watcher = LiveFileWatcher(
        missing,
        poll_interval=0.001,
        stable_checks=1,
    )

    with pytest.raises(FileNotFoundError):
        watcher.scan()


def test_live_file_watcher_rejects_invalid_poll_interval(tmp_path):
    with pytest.raises(ValueError):
        LiveFileWatcher(tmp_path, poll_interval=0)


def test_live_file_watcher_rejects_invalid_stable_checks(tmp_path):
    with pytest.raises(ValueError):
        LiveFileWatcher(tmp_path, stable_checks=0)


def test_live_file_watcher_ignores_existing_files_by_default(tmp_path):
    frame = tmp_path / "Image000001.dat"
    frame.write_bytes(b"existing frame")

    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
    )

    assert watcher.scan() == []


def test_live_file_watcher_can_process_existing_files(tmp_path):
    frame = tmp_path / "Image000001.dat"
    frame.write_bytes(b"existing frame")

    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
        process_existing=True,
    )

    assert watcher.scan() == [frame]


def test_live_file_watcher_detects_new_files_after_startup(tmp_path):
    existing = tmp_path / "Image000001.dat"
    existing.write_bytes(b"existing frame")

    watcher = LiveFileWatcher(
        tmp_path,
        poll_interval=0.001,
        stable_checks=1,
    )

    new_frame = tmp_path / "Image000002.dat"
    new_frame.write_bytes(b"new frame")

    assert watcher.scan() == [new_frame]