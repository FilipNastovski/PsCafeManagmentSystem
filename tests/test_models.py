"""Unit tests for models — dataclass serialization and helpers."""
import pytest

from models import Device, Session, DeviceStatus, SessionType, SessionStatus


class TestDeviceRoundTrip:
    def test_to_dict_and_from_dict(self):
        device = Device(
            id=1, name="PS1", price_per_hour=100, status="available",
            created_at="2026-01-01T00:00:00", is_disabled=False,
        )
        data = device.to_dict()
        restored = Device.from_dict(data)
        assert restored.id == device.id
        assert restored.name == device.name
        assert restored.price_per_hour == device.price_per_hour
        assert restored.status == device.status

    def test_from_dict_defaults(self):
        data = {"id": 1, "name": "PS2", "price_per_hour": 150}
        device = Device.from_dict(data)
        assert device.status == "available"
        assert device.is_disabled is False


class TestSessionRoundTrip:
    def test_to_dict_and_from_dict(self):
        session = Session(
            id=1, device_id=1, session_type="timed",
            start_time="2026-01-01T10:00:00",
            expected_end_time="2026-01-01T11:00:00",
            status="active", billed_minutes=60, final_price=100,
            acknowledged=False, device_name="PS1",
        )
        data = session.to_dict()
        restored = Session.from_dict(data)
        assert restored.id == session.id
        assert restored.device_id == session.device_id
        assert restored.session_type == session.session_type
        assert restored.final_price == session.final_price

    def test_from_dict_defaults(self):
        data = {"id": 1, "device_id": 1, "session_type": "open", "start_time": "2026-01-01T10:00:00"}
        session = Session.from_dict(data)
        assert session.status == "active"
        assert session.billed_minutes == 0
        assert session.final_price == 0

    def test_acknowledged_bool_conversion(self):
        data = {"id": 1, "device_id": 1, "session_type": "timed",
                "start_time": "2026-01-01T10:00:00", "acknowledged": 1}
        session = Session.from_dict(data)
        assert session.acknowledged is True


class TestSessionHelpers:
    def test_is_timed(self):
        s = Session(id=1, device_id=1, session_type="timed", start_time="now")
        assert s.is_timed() is True
        assert s.is_open() is False

    def test_is_open(self):
        s = Session(id=1, device_id=1, session_type="open", start_time="now")
        assert s.is_open() is True
        assert s.is_timed() is False

    def test_is_active(self):
        s = Session(id=1, device_id=1, session_type="timed", start_time="now", status="active")
        assert s.is_active() is True

    def test_is_active_overdue(self):
        s = Session(id=1, device_id=1, session_type="timed", start_time="now", status="overdue")
        assert s.is_active() is True

    def test_is_completed(self):
        s = Session(id=1, device_id=1, session_type="timed", start_time="now", status="completed")
        assert s.is_completed() is True
        assert s.is_active() is False

    def test_is_overdue(self):
        s = Session(id=1, device_id=1, session_type="timed", start_time="now", status="overdue")
        assert s.is_overdue() is True


class TestEnums:
    def test_device_status_values(self):
        assert DeviceStatus.AVAILABLE.value == "available"
        assert DeviceStatus.IN_USE.value == "in_use"
        assert DeviceStatus.OVERDUE.value == "overdue"
        assert DeviceStatus.DISABLED.value == "disabled"

    def test_session_type_values(self):
        assert SessionType.TIMED.value == "timed"
        assert SessionType.OPEN.value == "open"

    def test_session_status_values(self):
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.OVERDUE.value == "overdue"
        assert SessionStatus.CANCELLED.value == "cancelled"
