"""Shared test fixtures."""
import sys
import os
import pytest

# Ensure project root is on sys.path so `db`, `services`, `models` imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def test_db(tmp_path):
    """Create an isolated temp SQLite DB for each test.

    Patches db.DB_PATH to a temp file, resets the thread-local connection,
    and initializes the schema.  Cleans up after the test.
    """
    import db

    db_path = str(tmp_path / "test.db")
    db.set_db_path(db_path)
    db.reset_connection()
    db.init_database()
    yield db_path
    db.reset_connection()


@pytest.fixture
def sample_device(test_db):
    """Create a sample device and return its dict."""
    import db

    device_id = db.create_device("PS1", 100)
    return db.get_device(device_id)


@pytest.fixture
def sample_session(test_db, sample_device):
    """Create a timed session on the sample device and return its dict."""
    import db
    from datetime import datetime, timedelta

    end_time = (datetime.now() + timedelta(minutes=60)).isoformat()
    session_id = db.create_session(sample_device["id"], "timed", end_time)
    return db.get_session(session_id)
