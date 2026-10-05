"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Live Build Monitor
===============================================================================

Coordinates live .dat file ingestion, melt-pool processing, layer tracking,
and live build state tracking.

Responsibilities:
- Watch for new RPM222XR .dat files
- Process each new file through MeltPoolPipeline
- Track processed MeltPoolResults
- Track physical layer transitions
- Update BuildStateManager with processed frame state
- Provide live build statistics

This class does not perform anomaly detection, visualization, or G-code
control. Those systems will consume the state maintained here later.

===============================================================================
"""

from pathlib import Path

from enums import FrameStatus
from models import Frame

from monitoring.build_state_manager import BuildStateManager
from monitoring.layer_tracker import LayerTracker
from monitoring.live_file_watcher import LiveFileWatcher

from pipeline.classifier import MeltPoolClassification
from pipeline.pipeline import MeltPoolPipeline


class LiveBuildMonitor:
    """
    Coordinates live file ingestion, frame processing, layer tracking,
    and build state.

    Workflow:

        .dat file
            ↓
        LiveFileWatcher
            ↓
        LiveBuildMonitor
            ↓
        MeltPoolPipeline
            ↓
        MeltPoolResult
            ↓
        LayerTracker
            ↓
        BuildStateManager
            ↓
        BuildState
    """

    def __init__(
        self,
        directory: str | Path,
        pipeline: MeltPoolPipeline | None = None,
        state_manager: BuildStateManager | None = None,
        layer_tracker: LayerTracker | None = None,
        poll_interval: float = 0.1,
        stable_checks: int = 2,
        process_existing: bool = False,
    ):
        self.directory = Path(directory)

        self.pipeline = (
            pipeline
            if pipeline is not None
            else MeltPoolPipeline()
        )

        self.state_manager = (
            state_manager
            if state_manager is not None
            else BuildStateManager()
        )

        self.layer_tracker = (
            layer_tracker
            if layer_tracker is not None
            else LayerTracker()
        )

        self.watcher = LiveFileWatcher(
            self.directory,
            poll_interval=poll_interval,
            stable_checks=stable_checks,
            process_existing=process_existing,
        )

        self.results = []

        self._next_frame_number = 1

    def scan_once(self):
        """
        Detect and process all new stable .dat files.

        Layer transitions are detected when an active frame follows a
        sustained LASER_OFF period.

        Returns
        -------
        list[MeltPoolResult]
            Results produced during this scan.
        """

        files = self.watcher.scan()

        processed_results = []

        for file_path in files:
            frame_number = self._next_frame_number

            result = self.pipeline.process_file(
                file_path,
                frame_number=frame_number,
            )

            self.results.append(result)
            processed_results.append(result)

            layer_transition = self.layer_tracker.update(
                result.classification
            )

            # The transition is reported on the first active frame of the
            # new layer. Start that layer BEFORE recording this frame so the
            # frame belongs to the correct layer.
            if layer_transition:
                self.state_manager.start_new_layer()

            self._record_frame(
                file_path=file_path,
                frame_number=frame_number,
            )

            self._next_frame_number += 1

        return processed_results

    def _record_frame(
        self,
        file_path: Path,
        frame_number: int,
    ) -> None:
        """
        Record a successfully processed frame in BuildStateManager.

        The BuildState currently tracks frame identity and processing state.
        MeltPoolResult remains the source of detailed melt-pool measurements
        until the final Frame/Measurement data model is established.
        """

        frame = Frame(
            index=frame_number,
            path=file_path,
            status=FrameStatus.VALID,
        )

        self.state_manager.add_frame(frame)

    def reset(self) -> None:
        """
        Reset the monitor for a new build.
        """

        self.watcher.reset()
        self.state_manager.reset()
        self.layer_tracker.reset()

        self.results.clear()

        self._next_frame_number = 1

    @property
    def frames_processed(self) -> int:
        return self.state_manager.frames_processed

    @property
    def latest_result(self):
        if not self.results:
            return None
        return self.results[-1]

    @property
    def current_frame(self) -> int:
        return self.state_manager.current_frame

    @property
    def current_layer_number(self) -> int:
        return self.state_manager.current_layer_number

    @property
    def current_layer(self):
        return self.state_manager.current_layer

    @property
    def layers_completed(self) -> int:
        return self.state_manager.layers_completed

    @property
    def is_active(self) -> bool:
        return self.state_manager.is_active

    @property
    def machine_status(self) -> str:
        return self.state_manager.machine_status

    @property
    def classification_counts(
        self,
    ) -> dict[MeltPoolClassification, int]:
        counts = {
            classification: 0
            for classification in MeltPoolClassification
        }

        for result in self.results:
            counts[result.classification] += 1

        return counts

    @property
    def classification_summary(self) -> dict[str, int]:
        return {
            classification.value: count
            for classification, count
            in self.classification_counts.items()
        }