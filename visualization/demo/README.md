# Local MPAP demo

Feature development is frozen. The approved presentation exception uses Turbo false color on the existing sampled pixels, with a fixed27,000–55,000 intensity window. No runtime thresholds or research logic changed.

Install root requirements and run from the repository root:

```sh
.venv/bin/python -B visualization/demo/app.py --port 8771
```

Open http://127.0.0.1:8771 in one tab. Choose Folder Simulation, select an authorized local G-code file and an empty local receiving directory, and press Start. Absolute-path entry is supported; optional Browse requires Tkinter. No example raw files or machine program are distributed.

## Sources and external inputs

`FolderSimulationSource` uses the unchanged decoder and `MeltPoolPipeline.process_decoded`. The preview uses that same decoded array, never a second decode. It samples every nth row/column to keep the longest dimension≤192. Display indices are floor(255×clip((intensity−27000)/28000,0,1)); OpenCV's existing Turbo table produces RGB bytes. Values below/above the fixed window saturate. No interpolation or per-frame autoscaling. Measurements retain full-resolution pixels. False color means intensity, not calibrated temperature.

G-code is metadata only, never input to thermal inference. Valid files are processed once per session in numeric filename order. Stable metadata and header-derived payload size are required. Incomplete files retry; invalid data blocks. Gaps wait; duplicate/late/changed files error. No arrivals never creates OFF observations. Start replaces state and includes existing files again; Stop is not physical completion. The server is local/single-threaded, one session, without persistent resume.

`ReplaySource` uses optional external artifacts configured before launching:

```sh
export MPAP_REPLAY_FEATURES="/path/to/private/frame_features.csv"
export MPAP_REPLAY_TRACE="/path/to/private/causal_trace.jsonl"
.venv/bin/python -B visualization/demo/app.py --port 8771
```

CSV rows require contiguous one-based `frame`, unique `filename`, `classification`, and finite nonnegative `area_px`, `aspect_ratio`, `circularity`, `band3`, `band4`, `band5`. The JSONL trace must conform to the T0/T1/T2/T3/CENSORED schedule and evidence schema validated in `replay_source.py`; arbitrary recordings cannot be replayed by supplying an unrelated trace. Artifact generation is separate research work. These files and private meeting guides are not bundled. Without them replay reports unconfigured; use Folder Simulation. Folder monitoring does not need artifacts, a current working directory outside the clone, or any files from a developer's machine.

## Tests and limits

```sh
.venv/bin/python -B visualization/demo/test_folder_source.py
.venv/bin/python -B visualization/demo/test_thermal_preview.py
```

Tests generate temporary fixtures. Optional private artifact parity is explicitly skipped unless configured. The preview adds RGB bytes via base64 JSON, not an image dependency: OpenCV and NumPy are already pipeline requirements. Browser polling is roughly10Hz, file scanning roughly4Hz; this is not certified60fps operation. It displays the latest image, not every processed image. Small sampled features may be missed; rolling plots remain primary.
