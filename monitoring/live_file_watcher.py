"""
===============================================================================
MPAP
Melt Pool Analysis Platform
===============================================================================

Live File Watcher

Detects RPM222XR .dat files appearing in a directory.

The watcher is intentionally responsible only for file ingestion.

It does not:
    - decode .dat files
    - process frames
    - classify melt pools
    - update build state
    - detect anomalies
    - control the machine

Those responsibilities belong to other MPAP components.

===============================================================================
"""

from pathlib import Path
import time
from typing import Iterator


class LiveFileWatcher:
    """
    Watches a directory for RPM222XR .dat files.

    Parameters
    ----------
    directory : str | Path
        Directory containing the RPM222XR .dat output.

    poll_interval : float
        Number of seconds between directory checks.

    stable_checks : int
        Number of consecutive checks for which a file's size must remain
        unchanged before the file is considered ready.

    process_existing : bool
        If True, files already present when the watcher starts are eligible
        for processing.

        If False, files already present when the watcher starts are treated
        as already seen, and only files appearing after startup are detected.

        This defaults to False because live production monitoring should not
        automatically reprocess an existing build.
    """

    def __init__(
        self,
        directory: str | Path,
        poll_interval: float = 0.1,
        stable_checks: int = 2,
        process_existing: bool = False,
    ):
        self.directory = Path(directory)

        if poll_interval <= 0:
            raise ValueError(
                "poll_interval must be greater than 0."
            )

        if stable_checks <= 0:
            raise ValueError(
                "stable_checks must be greater than 0."
            )

        self.poll_interval = poll_interval
        self.stable_checks = stable_checks
        self.process_existing = process_existing

        self._seen: set[Path] = set()
        self._initialized = False

        # Establish the startup baseline immediately when the directory
        # already exists. This allows files created after watcher startup
        # to be distinguished from files that were already present.
        #
        # If the directory does not exist yet, defer validation until scan().
        if self.directory.exists():
            self._validate_directory()
            self._initialize_seen_files()

    def scan(self) -> list[Path]:
        """
        Return newly detected, ready-to-process .dat files.

        Files are returned in filename order.

        Returns
        -------
        list[Path]
            Newly detected stable .dat files.
        """

        self._validate_directory()

        if not self._initialized:
            self._initialize_seen_files()

        files = self._dat_files()

        new_files = []

        for path in files:
            if path in self._seen:
                continue

            if not self._is_stable(path):
                continue

            self._seen.add(path)
            new_files.append(path)

        return new_files

    def watch(self) -> Iterator[Path]:
        """
        Continuously yield newly detected .dat files.

        This generator blocks while waiting for new files.

        Yields
        ------
        Path
            A newly detected stable .dat file.
        """

        while True:
            for path in self.scan():
                yield path

            time.sleep(self.poll_interval)

    def mark_seen(self, path: str | Path) -> None:
        """
        Mark a file as already processed.
        """

        self._seen.add(Path(path))

    def reset(self) -> None:
        """
        Forget all previously seen files.

        After reset, existing files become eligible for processing.
        """

        self._seen.clear()
        self._initialized = True

    def _initialize_seen_files(self) -> None:
        """
        Establish the initial file baseline.

        In live mode, files already present are marked as seen.

        In processing/replay mode, existing files remain eligible for
        processing.
        """

        if not self.process_existing:
            self._seen.update(self._dat_files())

        self._initialized = True

    def _dat_files(self) -> list[Path]:
        """
        Return all .dat files currently present in the directory.
        """

        return sorted(
            path
            for path in self.directory.glob("*.dat")
            if path.is_file()
        )

    def _validate_directory(self) -> None:
        """
        Validate the configured watch directory.
        """

        if not self.directory.exists():
            raise FileNotFoundError(
                f"Watch directory does not exist: {self.directory}"
            )

        if not self.directory.is_dir():
            raise NotADirectoryError(
                f"Watch path is not a directory: {self.directory}"
            )

    def _is_stable(self, path: Path) -> bool:
        """
        Determine whether a file has stopped growing.

        A file must report the same size for ``stable_checks`` consecutive
        checks before it is considered ready for processing.
        """

        previous_size = -1
        stable_count = 0

        while stable_count < self.stable_checks:
            try:
                current_size = path.stat().st_size
            except FileNotFoundError:
                return False

            if current_size == previous_size:
                stable_count += 1
            else:
                stable_count = 0
                previous_size = current_size

            if stable_count < self.stable_checks:
                time.sleep(self.poll_interval)

        return True