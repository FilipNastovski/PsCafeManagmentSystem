# PlayStation Café Management System

A lightweight desktop application for managing PlayStation devices in a café. Track sessions, handle billing, and generate reports — all offline, all local.

## Features

- **Dashboard** — View all devices with real-time status, elapsed time, and estimated cost
- **Session Management** — Start timed (fixed duration) or open-ended sessions
- **Pricing** — Automatic minute-based billing in MKD, rounds up to the nearest minute
- **Alerts** — Sound notification when timed sessions expire, with mute toggle
- **Reports** — Today, Week, Month, or custom date ranges; filter by device
- **Device Management** — Add, edit, or remove devices with custom hourly rates

## Download

Get the latest release for Windows from the [Releases](../../releases) page. No installation required — just extract and run.

## Usage

### Starting a Session
1. Click **Start** on an available device card
2. Choose **Timed** (fixed duration) or **Open** (no time limit)
3. For timed sessions, select the duration in minutes and confirm

### Ending a Session
1. Click **End** on an active device
2. Review the session summary (duration, price)
3. Optionally **Extend** the session if more time is needed
4. Confirm to end and calculate the final price

### Managing Devices
1. Click **Manage Devices**
2. **Add** new devices (auto-named PS1, PS2, etc.) with custom hourly rates
3. **Edit** existing device names or prices
4. **Delete** devices (only if no active session)

### Viewing Reports
1. Click **Reports**
2. Select a period: **Today**, **Week**, **Month**, or **Custom**
3. Optionally filter by device
4. Click **Refresh** to update

---

## Development

### Requirements

- Python 3.10+
- PySide6
- pytest + pytest-qt (for testing)

### Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate.ps1   # Windows
source .venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

The database (`pscafe.db`) and log (`pscafe.log`) are created in the project root during development.

### Test

```bash
# All tests
pytest

# Single file
pytest tests/test_session_service.py -v

# Single test
pytest tests/test_pricing_service.py -k test_exact_hour
```

### Build Standalone Executable

```bash
# Windows
.\build.bat

# Linux/macOS
./build.sh
```

Output: `dist/PS-Cafe-Manager/` — a folder containing the executable and all dependencies. Users download and run the `.exe` directly.

### Project Structure

```
├── main.py              # Entry point (QApplication, DB init, session recovery)
├── db/                  # SQLite layer (thread-local, WAL mode)
├── models/              # Dataclasses + enums
├── services/            # Business logic (SessionService, PricingService, etc.)
├── ui/                  # PySide6 widgets
├── utils/               # Path resolution (dev vs packaged)
├── resources/           # icon.png, icon.ico, alert.wav
├── tests/               # pytest suite
├── build.spec           # PyInstaller configuration
└── build.bat / build.sh # Build scripts
```

### Path Resolution

The app uses `utils/app_path.py` to handle file paths differently in dev vs packaged mode:

| Path | Development | Packaged |
|------|-------------|----------|
| Database | `project_root/pscafe.db` | `%APPDATA%/PsCafeManagement/pscafe.db` (Win) |
| Log | `project_root/pscafe.log` | `%APPDATA%/PsCafeManagement/pscafe.log` (Win) |
| Resources | `project_root/resources/` | `sys._MEIPASS/resources/` |

When adding new file references, always use `get_data_path()` for writable files and `get_resource_path()` for bundled read-only assets.

### Packaging

PyInstaller uses `--onedir` mode (defined in `build.spec`). The `resources/` directory is bundled into `_internal/resources/` at build time. The executable icon is `resources/icon.ico`.

### Architecture Notes

- **Currency**: MKD (Macedonian Denar), stored as integer
- **Billing**: `(price_per_hour * minutes) // 60`, rounds up to whole minute
- **Session types**: `timed` (has `expected_end_time`) and `open` (no time limit)
- **Device statuses**: `available`, `in_use`, `overdue`, `disabled`
- **Session recovery**: On startup, active sessions are restored; timed sessions past their end time are marked `overdue`
- **Single-instance**: Enforced via `QLockFile`

### Development Workflow

#### Implementing a New Feature

1. **Write tests first** — add to the relevant `tests/test_*.py` file (create a new one if needed)
2. **Run tests** to confirm they fail: `pytest tests/test_your_file.py -v`
3. **Implement the feature** in the source code
4. **Run affected tests**: `pytest tests/test_your_file.py -v`
5. **Run full suite** to catch regressions: `pytest`

#### Revising Existing Code

1. **Run full suite** to confirm green: `pytest`
2. **Make changes**
3. **Run affected tests** — pick the relevant file: `pytest tests/test_session_service.py -v`
4. **Run full suite**: `pytest`

#### Releasing an Update

1. **Run full suite**: `pytest`
2. **Build**: `.\build.bat` (or `./build.sh` on Linux/macOS)
3. **Test the packaged app**: run `dist/PS-Cafe-Manager/PS-Cafe-Manager.exe`
4. **Verify data location**: check `%APPDATA%/PsCafeManagement/` for `pscafe.db` and `pscafe.log`
5. **Zip** the `PS-Cafe-Manager/` folder and attach to a GitHub Release

#### Test File Placement

| Test type | Where to put it | Notes |
|-----------|-----------------|-------|
| Pure logic (no DB) | `test_pricing_service.py` or new `test_*.py` | No fixture needed |
| DB-dependent | Any `test_*.py` | Must use `test_db` fixture |
| UI widgets | Any `test_*.py` | Use `pytest-qt` with `qtbot` fixture |
| Path helpers | `test_app_path.py` | Use `monkeypatch` for frozen mode |
