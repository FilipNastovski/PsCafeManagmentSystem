# PsCafeManagmentSystem - Agent Guide

## Developer Commands

```bash
# Run the app
python main.py

# Build standalone executable
./build.bat        # Windows
./build.sh         # Linux/macOS
```

Verify by running the app or tests — there is no linter, typechecker, or CI.

## Architecture

- **Entry point**: `main.py` — sets up QApplication, inits DB, recovers sessions, shows MainWindow
- **`db/`** — SQLite layer (thread-local connections, WAL mode). All SQL lives here. Schema auto-created via `CREATE TABLE IF NOT EXISTS` — no migrations.
- **`models/`** — Pure dataclasses + enums (`Device`, `Session`, `DeviceStatus`, `SessionType`, `SessionStatus`). Not used by the DB layer directly (it returns dicts).
- **`services/`** — Business logic: `SessionService`, `PricingService`, `ReportService`, `AlertService`
- **`ui/`** — PySide6 widgets: `MainWindow`, `SessionDialog`, `EndSessionDialog`, `ExtendDialog`, `DeviceDialog`, `ReportWindow`
- **`utils/`** — Path resolution helpers (`app_path.py`) for dev vs packaged mode
- **`resources/`** — `alert.wav` (sound notification), `icon.png`, `icon.ico` (Windows exe icon)

## Key Conventions

- **Currency**: MKD (Macedonian Denar), stored as integer (no decimals)
- **Pricing**: per-device `price_per_hour` in DB; billing rounds up to whole minute, `(price * minutes) // 60`
- **Session types**: `timed` (has `expected_end_time`) and `open` (no time limit)
- **Device statuses**: `available`, `in_use`, `overdue`, `disabled`
- **Session statuses**: `active`, `completed`, `overdue`, `cancelled`
- **Device names**: auto-generated as `PS1`, `PS2`, etc. via `get_next_device_number()`
- **Single-instance**: enforced via `QLockFile` — only one app instance allowed
- **Logging**: `pscafe.log`, 5MB rotation, 3 backups

## Path Resolution

All file paths go through `utils/app_path.py` — never use raw `os.path.join(..., "__file__")` patterns.

```python
from utils.app_path import get_data_path, get_resource_path

# Writable data (DB, logs) — project root in dev, platformdirs when packaged
db_path = get_data_path("pscafe.db")
log_path = get_data_path("pscafe.log")

# Bundled read-only resources (icons, sounds)
icon = get_resource_path("resources/icon.png")
alert = get_resource_path("resources/alert.wav")
```

**Dev mode**: data and resources resolve to the project root directory.
**Packaged mode** (`sys.frozen = True`):
- Data → `%APPDATA%/PsCafeManagement/` (Windows) or `~/.local/share/PsCafeManagement/` (Linux)
- Resources → `sys._MEIPASS` (PyInstaller temp extract dir)

## Database

- File: `pscafe.db` — project root in dev, `%APPDATA%/PsCafeManagement/` when packaged (gitignored)
- Tables: `devices`, `sessions`
- Thread-local connections via `threading.local()` — do not share connections across threads
- WAL journal mode, 10s busy timeout
- `init_database()` called at startup; `close_connection()` called on exit

## Session Recovery

On startup, `SessionService.recover_active_sessions()` restores sessions that were active when the app last closed — marks timed sessions past their end time as `overdue`, ensures device statuses are correct.

## Packaging

- **Tool**: PyInstaller (`--onedir` mode via `build.spec`)
- **Output**: `dist/PS-Cafe-Manager/` folder containing `PS-Cafe-Manager.exe` + `_internal/`
- **Build command**: `./build.bat` (Windows) or `./build.sh` (Linux/macOS)
- **Icon**: `resources/icon.ico` embedded in the Windows executable
- **Bundled data**: `resources/` directory included via `datas=[('resources', 'resources')]` in `build.spec`
- **Dependencies**: `platformdirs` for cross-platform data directories, `pyinstaller` for building

### Release workflow
1. Build: `./build.bat`
2. Test the output in `dist/PS-Cafe-Manager/`
3. Zip the `PS-Cafe-Manager/` folder and attach to a GitHub Release

## Gotchas

- `requirements.txt` is binary on Windows — use `pip install PySide6` if it fails to read
- Alert service uses platform-specific sound APIs: `winsound` (Windows), `aplay`/`paplay` (Linux), `afplay` (macOS)
- PyInstaller on Windows requires `icon.ico` (not `.png`) for the executable icon
- `get_resource_path()` uses forward slashes in the argument (e.g., `"resources/icon.png"`) — it normalizes to OS separators via `os.path.normpath()`

## Testing

Run all tests: `pytest` or `python -m pytest`

Run a single file: `pytest tests/test_pricing_service.py`
Run a single test: `pytest tests/test_pricing_service.py -k test_exact_hour`

- **Framework**: pytest + pytest-qt (PySide6 UI tests)
- **DB isolation**: `tests/conftest.py` provides `test_db` fixture that patches `db.DB_PATH` to a temp file and resets thread-local connections. Each test gets a fresh SQLite DB.
- **Helpers**: `sample_device` and `sample_session` fixtures build on `test_db`
- **Structure**: tests across different files — app_path (9), pricing (20), models (10), db (23), session_service (17), report_service (11), ui_main_window (7), ui_session_dialog (7), ui_end_session_dialog (4)
- **UI tests**: Use `qtbot` fixture; mouse clicks require `Qt.MouseButton.LeftButton` not string `"left"`
- **Adding tests**: New DB-dependent tests must use `test_db` fixture; pure unit tests need no fixture
- **Path tests**: `test_app_path.py` uses `monkeypatch` to simulate frozen mode (`sys.frozen`, `sys._MEIPASS`)

## Workflow

### Adding a New Feature
1. **Write tests first** — add to the relevant `tests/test_*.py` file (create a new one if needed)
2. **Run tests** to confirm they fail: `pytest tests/test_your_file.py -v`
3. **Implement the feature** in the source code
4. **Run affected tests**: `pytest tests/test_your_file.py -v`
5. **Run full suite** to catch regressions: `pytest`
6. **Update AGENTS.md** if the feature introduces new conventions, commands, or gotchas

### Revising Existing Code
1. **Run full suite** to confirm green: `pytest`
2. **Make changes**
3. **Run affected tests** — pick the relevant file: `pytest tests/test_session_service.py -v`
4. **Run full suite**: `pytest`

### Building a Release
1. **Run full suite**: `pytest`
2. **Build**: `./build.bat` (or `./build.sh` on Linux/macOS)
3. **Test the packaged app**: run `dist/PS-Cafe-Manager/PS-Cafe-Manager.exe`
4. **Verify data location**: check `%APPDATA%/PsCafeManagement/` for `pscafe.db` and `pscafe.log`

### Test File Placement
- **Pure logic** (no DB) → `test_pricing_service.py` or new `test_*.py`
- **DB-dependent** → use `test_db` fixture from `conftest.py`
- **UI widgets** → use `pytest-qt` with `qtbot` fixture
- **Path helpers** → `test_app_path.py` (use `monkeypatch` for frozen mode)

### When to Update AGENTS.md
Update only when you discover something a future agent would likely miss: new commands, architectural patterns, testing quirks, or gotchas. Skip obvious changes.

## AI Agent Workflow

### Before Making Any Changes
1. **Read the relevant files** — use `Read` and `Grep` to understand existing patterns before editing
2. **Check existing tests** — see how similar features are tested in `tests/`
3. **Run `pytest`** — confirm the suite is green before you start

### Implementing a Feature
1. **Write tests first** — add to the relevant `tests/test_*.py` or create a new one
2. **Run tests** to confirm they fail: `pytest tests/test_your_file.py -v`
3. **Implement** — follow existing code style, use `get_data_path()` / `get_resource_path()` for file paths
4. **Run affected tests**: `pytest tests/test_your_file.py -v`
5. **Run full suite**: `pytest` — do not skip this
6. **Update AGENTS.md** if conventions, commands, or gotchas changed

### Fixing a Bug
1. **Run full suite** to confirm current state: `pytest`
2. **Reproduce the bug** — understand the root cause before editing
3. **Write a test** that reproduces the bug (should fail)
4. **Fix the code**
5. **Run affected tests**, then **full suite**: `pytest`

### Modifying Existing Code
1. **Run full suite** to confirm green: `pytest`
2. **Read the file and its imports** — understand dependencies before changing anything
3. **Make changes** — match existing style, no comments unless asked
4. **Run affected tests**, then **full suite**: `pytest`

### Building a Release
1. **Run full suite**: `pytest`
2. **Build**: `./build.bat` (or `./build.sh` on Linux/macOS)
3. **Test the packaged app**: run `dist/PS-Cafe-Manager/PS-Cafe-Manager.exe`
4. **Verify data location**: check `%APPDATA%/PsCafeManagement/` for `pscafe.db` and `pscafe.log`

### Rules
- **Never commit** unless explicitly asked
- **Never guess imports** — read existing files to see what's available
- **Never skip tests** — if tests fail, fix them before declaring done
- **Never use raw path joins** — always go through `utils/app_path.py`
- **Minimal comments** in code, but add where necessary
