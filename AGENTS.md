# PsCafeManagmentSystem - Agent Guide

## Developer Commands

```bash
# Run the app
python main.py

# On Linux (auto-creates venv if missing)
./run.sh
```

Verify by running the app or tests — there is no linter, typechecker, or CI.

## Architecture

- **Entry point**: `main.py` — sets up QApplication, inits DB, recovers sessions, shows MainWindow
- **`db/`** — SQLite layer (thread-local connections, WAL mode). All SQL lives here. Schema auto-created via `CREATE TABLE IF NOT EXISTS` — no migrations.
- **`models/`** — Pure dataclasses + enums (`Device`, `Session`, `DeviceStatus`, `SessionType`, `SessionStatus`). Not used by the DB layer directly (it returns dicts).
- **`services/`** — Business logic: `SessionService`, `PricingService`, `ReportService`, `AlertService`
- **`ui/`** — PySide6 widgets: `MainWindow`, `SessionDialog`, `EndSessionDialog`, `ExtendDialog`, `DeviceDialog`, `ReportWindow`
- **`resources/`** — `alert.wav` (sound notification), `icon.png`

## Key Conventions

- **Currency**: MKD (Macedonian Denar), stored as integer (no decimals)
- **Pricing**: per-device `price_per_hour` in DB; billing rounds up to whole minute, `(price * minutes) // 60`
- **Session types**: `timed` (has `expected_end_time`) and `open` (no time limit)
- **Device statuses**: `available`, `in_use`, `overdue`, `disabled`
- **Session statuses**: `active`, `completed`, `overdue`, `cancelled`
- **Device names**: auto-generated as `PS1`, `PS2`, etc. via `get_next_device_number()`
- **Single-instance**: enforced via `QLockFile` — only one app instance allowed
- **Logging**: `pscafe.log`, 5MB rotation, 3 backups

## Database

- File: `pscafe.db` at project root (gitignored)
- Tables: `devices`, `sessions`
- Thread-local connections via `threading.local()` — do not share connections across threads
- WAL journal mode, 10s busy timeout
- `init_database()` called at startup; `close_connection()` called on exit

## Session Recovery

On startup, `SessionService.recover_active_sessions()` restores sessions that were active when the app last closed — marks timed sessions past their end time as `overdue`, ensures device statuses are correct.

## Gotchas

- `run.sh` is Linux-focused (`source .venv/bin/activate`). On Windows, activate with `.venv\Scripts\activate.ps1` then `python main.py`
- `requirements.txt` is binary on Windows — use `pip install PySide6` if it fails to read
- Alert service uses platform-specific sound APIs: `winsound` (Windows), `aplay`/`paplay` (Linux), `afplay` (macOS)

## Testing

Run all tests: `pytest` or `python -m pytest`

Run a single file: `pytest tests/test_pricing_service.py`
Run a single test: `pytest tests/test_pricing_service.py -k test_exact_hour`

- **Framework**: pytest + pytest-qt (PySide6 UI tests)
- **DB isolation**: `tests/conftest.py` provides `test_db` fixture that patches `db.DB_PATH` to a temp file and resets thread-local connections. Each test gets a fresh SQLite DB.
- **Helpers**: `sample_device` and `sample_session` fixtures build on `test_db`
- **Structure**: tests across different files — pricing (20), models (10), db (23), session_service (17), report_service (11), ui_main_window (7), ui_session_dialog (7), ui_end_session_dialog (4)
- **UI tests**: Use `qtbot` fixture; mouse clicks require `Qt.MouseButton.LeftButton` not string `"left"`
- **Adding tests**: New DB-dependent tests must use `test_db` fixture; pure unit tests need no fixture

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

### Test File Placement
- **Pure logic** (no DB) → `test_pricing_service.py` or new `test_*.py`
- **DB-dependent** → use `test_db` fixture from `conftest.py`
- **UI widgets** → use `pytest-qt` with `qtbot` fixture

### When to Update AGENTS.md
Update only when you discover something a future agent would likely miss: new commands, architectural patterns, testing quirks, or gotchas. Skip obvious changes.