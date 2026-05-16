"""Integration tests for SessionService — uses isolated test DB fixture."""
import pytest
from datetime import datetime, timedelta

import db
from services.session_service import SessionService


class TestStartTimedSession:
    def test_starts_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = SessionService.start_timed_session(device_id, 60)
        assert session_id is not None
        session = db.get_session(session_id)
        assert session["session_type"] == "timed"
        assert session["status"] == "active"
        assert session["expected_end_time"] is not None

    def test_device_becomes_in_use(self, test_db):
        device_id = db.create_device("PS1", 100)
        SessionService.start_timed_session(device_id, 60)
        device = db.get_device(device_id)
        assert device["status"] == "in_use"

    def test_raises_on_in_use_device(self, test_db):
        device_id = db.create_device("PS1", 100)
        SessionService.start_timed_session(device_id, 60)
        with pytest.raises(ValueError, match="already in use"):
            SessionService.start_timed_session(device_id, 30)

    def test_raises_on_nonexistent_device(self, test_db):
        with pytest.raises(ValueError, match="not found"):
            SessionService.start_timed_session(9999, 60)


class TestStartOpenSession:
    def test_starts_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = SessionService.start_open_session(device_id)
        session = db.get_session(session_id)
        assert session["session_type"] == "open"
        assert session["expected_end_time"] is None

    def test_raises_on_in_use_device(self, test_db):
        device_id = db.create_device("PS1", 100)
        SessionService.start_open_session(device_id)
        with pytest.raises(ValueError, match="already in use"):
            SessionService.start_open_session(device_id)

    def test_raises_on_nonexistent_device(self, test_db):
        with pytest.raises(ValueError, match="not found"):
            SessionService.start_open_session(9999)


class TestEndSession:
    def test_ends_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        result = SessionService.end_session(session_id)
        assert result["session_id"] == session_id
        assert result["final_price"] >= 0
        assert result["duration_minutes"] >= 1
        assert result["device_name"] == "PS1"

    def test_device_becomes_available(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        SessionService.end_session(session_id)
        device = db.get_device(device_id)
        assert device["status"] == "available"

    def test_raises_on_nonexistent_session(self, test_db):
        with pytest.raises(ValueError, match="not found"):
            SessionService.end_session(9999)


class TestExtendSession:
    def test_extends_timed_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        end_time = (datetime.now() + timedelta(minutes=30)).isoformat()
        session_id = db.create_session(device_id, "timed", end_time)
        new_end = SessionService.extend_session(session_id, 30)
        session = db.get_session(session_id)
        assert session["expected_end_time"] == new_end
        assert session["status"] == "active"

    def test_raises_on_open_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "open", None)
        with pytest.raises(ValueError, match="Cannot extend open-ended"):
            SessionService.extend_session(session_id, 30)

    def test_raises_on_nonexistent_session(self, test_db):
        with pytest.raises(ValueError, match="not found"):
            SessionService.extend_session(9999, 30)


class TestCheckAndMarkOverdue:
    def test_marks_expired_timed_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        past_end = (datetime.now() - timedelta(minutes=10)).isoformat()
        session_id = db.create_session(device_id, "timed", past_end)
        overdue_ids = SessionService.check_and_mark_overdue()
        assert session_id in overdue_ids
        session = db.get_session(session_id)
        assert session["status"] == "overdue"

    def test_does_not_mark_future_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        future_end = (datetime.now() + timedelta(hours=1)).isoformat()
        db.create_session(device_id, "timed", future_end)
        overdue_ids = SessionService.check_and_mark_overdue()
        assert len(overdue_ids) == 0

    def test_does_not_mark_open_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        db.create_session(device_id, "open", None)
        overdue_ids = SessionService.check_and_mark_overdue()
        assert len(overdue_ids) == 0


class TestRecoverActiveSessions:
    def test_restores_in_use_status(self, test_db):
        device_id = db.create_device("PS1", 100)
        end_time = (datetime.now() + timedelta(hours=1)).isoformat()
        db.create_session(device_id, "timed", end_time)
        db.update_device_status(device_id, "available")
        recovered = SessionService.recover_active_sessions()
        assert recovered == 1
        device = db.get_device(device_id)
        assert device["status"] == "in_use"

    def test_marks_past_due_as_overdue(self, test_db):
        device_id = db.create_device("PS1", 100)
        past_end = (datetime.now() - timedelta(minutes=30)).isoformat()
        session_id = db.create_session(device_id, "timed", past_end)
        recovered = SessionService.recover_active_sessions()
        assert recovered == 1
        session = db.get_session(session_id)
        assert session["status"] == "overdue"


class TestAcknowledgeAlert:
    def test_acknowledges(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        SessionService.acknowledge_alert(session_id)
        session = db.get_session(session_id)
        assert session["acknowledged"] == 1


class TestGetSessionDetails:
    def test_active_session_has_elapsed_and_price(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        details = SessionService.get_session_details(session_id)
        assert details is not None
        assert "elapsed_minutes" in details
        assert "current_price" in details
        assert details["device_name"] == "PS1"

    def test_completed_session_has_final_values(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(session_id, 100, 60)
        details = SessionService.get_session_details(session_id)
        assert details["billed_minutes"] == 60
        assert details["final_price"] == 100

    def test_returns_none_for_nonexistent(self, test_db):
        assert SessionService.get_session_details(9999) is None


class TestGetActiveSessionForDevice:
    def test_returns_active(self, test_db):
        device_id = db.create_device("PS1", 100)
        db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        result = SessionService.get_active_session_for_device(device_id)
        assert result is not None

    def test_returns_none(self, test_db):
        device_id = db.create_device("PS1", 100)
        assert SessionService.get_active_session_for_device(device_id) is None
