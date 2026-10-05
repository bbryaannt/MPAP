# MPAP — Melt Pool Analysis Platform

MPAP is development-stage software for monitoring RPM222XR thermal `.dat` frames during metal additive manufacturing. It processes thermal imagery, extracts melt-pool measurements, visualizes behavior, and supports research into build-state and anomaly detection.

## Implemented today

- Decode supported RPM222XR frames and extract melt-pool geometry and intensity-band counts.
- Assign existing rule-based frame categories.
- Monitor a local folder in the isolated demo, with conservative file-readiness checks, numeric ordering and explicit data-quality handling.
- Display a sampled thermal-intensity preview, rolling measurements and observed OFF-event evidence.
- Replay separately supplied, previously processed artifacts for deterministic research demonstrations.

Folder Simulation processes files arriving in a directory; it is not a live machine connection. G-code selection is configuration only and does not supply thermal transition decisions. The preview uses fixed 27,000–55,000 intensity scaling and Turbo false color; it is not calibrated temperature.

## Research and future work

Validated physical layer-transition detection, anomaly interpretation, independent machine-state verification, and eventual reviewed correction proposals remain research goals. This demo does not provide live machine control, automatic G-code correction, autonomous intervention, or production readiness. Transition inference remains unresolved.

## Local setup and launch

Use Python 3.11 or newer. From a fresh clone on macOS/Linux:

```sh
git clone https://github.com/bbryaannt/MPAP.git
cd MPAP
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B visualization/demo/app.py --port 8771
```

Open http://127.0.0.1:8771. Select Folder Simulation, a local G-code file, and a local thermal folder; press Start. No raw recordings, machine programs, private research outputs or local presentation files are included. Supply authorized inputs separately. Start a fresh session on an empty receiving folder to demonstrate arrivals. No incoming file is not a LASER_OFF observation.

The demo is loopback-only with one shared session. It does not persist recovery state. The optional native file chooser requires Tkinter; absolute path entry works without it. Windows uses `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

Artifact Replay is optional and requires separately supplied feature CSV and causal trace files. Without them the initial screen explains that replay is unconfigured; Folder Simulation can still be started. See [demo setup](visualization/demo/README.md) for configuration and limitations.

## Tests

```sh
.venv/bin/python -m pytest tests
.venv/bin/python -B visualization/demo/test_folder_source.py
.venv/bin/python -B visualization/demo/test_thermal_preview.py
```

The portable demo tests use temporary synthetic inputs. Private replay parity is skipped unless artifacts are configured. Some legacy executable inspection scripts require local research inputs and are not portable tests.

## Publication and license

Raw data, machine programs and research findings require separate publication review. A public repository is not a grant of rights to external inputs. No software license has been established or included; the repository owner must choose licensing terms before claiming an open-source license.
