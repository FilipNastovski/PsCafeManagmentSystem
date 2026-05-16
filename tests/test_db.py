"""Integration tests for the db layer — uses isolated test DB fixture."""
import pytest
from datetime import datetime, timedelta

import db


class TestDeviceCRUD:
    def test_create_device(self, test_db):
        device_id = db.create_device("PS1", 100)
        assert device_id is not None
        assert device_id > 0

    def test_get_device(self, test_db):
        device_id = db.create_device("PS1", 100)
        device = db.get_device(device_id)
        assert device is not None
        assert device["name"] == "PS1"
        assert device["price_per_hour"] == 100
        assert device["status"] == "available"

    def test_get_device_not_found(self, test_db):
        assert db.get_device(9999) is None

    def test_get_all_devices(self, test_db):
        db.create_device("PS1", 100)
        db.create_device("PS2", 150)
        devices = db.get_all_devices()
        assert len(devices) == 2

    def test_update_device(self, test_db):
        device_id = db.create_device("PS1", 100)
        result = db.update_device(device_id, "PS-Alpha", 200)
        assert result is True
        device = db.get_device(device_id)
        assert device["name"] == "PS-Alpha"
        assert device["price_per_hour"] == 200

    def test_update_device_not_found(self, test_db):
        assert db.update_device(9999, "X", 100) is False


class TestDeleteDevice:
    def test_delete_device(self, test_db):
        device_id = db.create_device("PS1", 100)
        assert db.delete_device(device_id) is True
        assert db.get_device(device_id) is None

    def test_delete_device_with_active_session_blocked(self, test_db):
        device_id = db.create_device("PS1", 100)
        db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        assert db.delete_device(device_id) is False
        assert db.get_device(device_id) is not None

    def test_delete_device_with_completed_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(session_id, 100, 60)
        assert db.delete_device(device_id) is True


class TestDeviceNaming:
    def test_get_next_device_number_empty(self, test_db):
        assert db.get_next_device_number() == 1

    def test_get_next_device_number_sequence(self, test_db):
        db.create_device("PS1", 100)
        assert db.get_next_device_number() == 2
        db.create_device("PS2", 100)
        assert db.get_next_device_number() == 3

    def test_device_name_exists(self, test_db):
        db.create_device("PS1", 100)
        assert db.device_name_exists("PS1") is True
        assert db.device_name_exists("PS2") is False

    def test_device_name_exists_exclude(self, test_db):
        device_id = db.create_device("PS1", 100)
        assert db.device_name_exists("PS1", exclude_device_id=device_id) is False


class TestDeviceStatus:
    def test_update_device_status(self, test_db):
        device_id = db.create_device("PS1", 100)
        db.update_device_status(device_id, "in_use")
        device = db.get_device(device_id)
        assert device["status"] == "in_use"


class TestSessionCRUD:
    def test_create_timed_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        end_time = (datetime.now() + timedelta(minutes=60)).isoformat()
        session_id = db.create_session(device_id, "timed", end_time)
        assert session_id is not None
        session = db.get_session(session_id)
        assert session["session_type"] == "timed"
        assert session["status"] == "active"

    def test_create_open_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "open", None)
        session = db.get_session(session_id)
        assert session["session_type"] == "open"
        assert session["expected_end_time"] is None

    def test_get_session_not_found(self, test_db):
        assert db.get_session(9999) is None

    def test_end_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        result = db.end_session(session_id, 100, 60)
        assert result is True
        session = db.get_session(session_id)
        assert session["status"] == "completed"
        assert session["final_price"] == 100
        assert session["billed_minutes"] == 60

    def test_end_session_not_found(self, test_db):
        assert db.end_session(9999, 0, 0) is False

    def test_end_session_sets_device_available(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(session_id, 100, 60)
        device = db.get_device(device_id)
        assert device["status"] == "available"


class TestActiveSession:
    def test_get_active_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        active = db.get_active_session(device_id)
        assert active is not None
        assert active["id"] == session_id

    def test_get_active_session_none(self, test_db):
        device_id = db.create_device("PS1", 100)
        assert db.get_active_session(device_id) is None

    def test_get_active_session_returns_overdue(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.mark_session_overdue(session_id)
        active = db.get_active_session(device_id)
        assert active is not None
        assert active["status"] == "overdue"

    def test_get_all_active_sessions(self, test_db):
        d1 = db.create_device("PS1", 100)
        d2 = db.create_device("PS2", 100)
        db.create_session(d1, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.create_session(d2, "open", None)
        sessions = db.get_all_active_sessions()
        assert len(sessions) == 2


class TestSessionState:
    def test_mark_session_overdue(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.mark_session_overdue(session_id)
        session = db.get_session(session_id)
        assert session["status"] == "overdue"

    def test_acknowledge_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.acknowledge_session(session_id)
        session = db.get_session(session_id)
        assert session["acknowledged"] == 1

    def test_extend_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        end_time = (datetime.now() + timedelta(minutes=30)).isoformat()
        session_id = db.create_session(device_id, "timed", end_time)
        new_end = (datetime.now() + timedelta(hours=2)).isoformat()
        db.extend_session(session_id, new_end)
        session = db.get_session(session_id)
        assert session["expected_end_time"] == new_end
        assert session["status"] == "active"


class TestSessionHistory:
    def test_get_session_history_all(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(session_id, 100, 60)
        history = db.get_session_history()
        assert len(history) == 1
        assert history[0]["device_name"] == "PS1"

    def test_get_session_history_filter_by_device(self, test_db):
        d1 = db.create_device("PS1", 100)
        d2 = db.create_device("PS2", 150)
        s1 = db.create_session(d1, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        s2 = db.create_session(d2, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(s1, 100, 60)
        db.end_session(s2, 150, 60)
        history = db.get_session_history(device_id=d1)
        assert len(history) == 1
        assert history[0]["device_name"] == "PS1"

    def test_get_session_history_filter_by_type(self, test_db):
        device_id = db.create_device("PS1", 100)
        s1 = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        s2 = db.create_session(device_id, "open", None)
        db.end_session(s1, 100, 60)
        db.end_session(s2, 100, 30)
        history = db.get_session_history(session_type="timed")
        assert len(history) == 1
        assert history[0]["session_type"] == "timed"

    def test_get_session_history_filter_by_status(self, test_db):
        device_id = db.create_device("PS1", 100)
        s1 = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(s1, 100, 60)
        db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=2)).isoformat())
        history = db.get_session_history(status_filter="completed")
        assert len(history) == 1


class TestReportSummary:
    def test_empty_summary(self, test_db):
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        summary = db.get_report_summary(start, end)
        assert summary["total_sessions"] == 0
        assert summary["total_revenue"] == 0

    def test_summary_with_sessions(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(session_id, 100, 60)
        now = datetime.now()
        start = (now - timedelta(days=1)).isoformat()
        end = (now + timedelta(days=1)).isoformat()
        summary = db.get_report_summary(start, end)
        assert summary["total_sessions"] == 1
        assert summary["total_minutes"] == 60
        assert summary["total_revenue"] == 100
        assert summary["most_used_device"] == "PS1"
