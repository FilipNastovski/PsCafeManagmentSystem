"""UI tests for SessionStartDialog — uses pytest-qt."""
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.session_dialog import SessionStartDialog


@pytest.fixture(autouse=True)
def setup_test_db(test_db):
    pass


class TestSessionStartDialog:
    def test_shows_device_name(self, qtbot):
        device = {"id": 1, "name": "PS1", "price_per_hour": 100, "status": "available"}
        dialog = SessionStartDialog(device)
        qtbot.add_widget(dialog)
        assert "PS1" in dialog.windowTitle()

    def test_shows_rate(self, qtbot):
        device = {"id": 1, "name": "PS1", "price_per_hour": 100, "status": "available"}
        dialog = SessionStartDialog(device)
        qtbot.add_widget(dialog)
        labels = dialog.findChildren(type(dialog._timed_price_label))
        assert any("100 MKD" in lbl.text() for lbl in labels)

    def test_timed_radio_checked_by_default(self, qtbot):
        device = {"id": 1, "name": "PS1", "price_per_hour": 100, "status": "available"}
        dialog = SessionStartDialog(device)
        qtbot.add_widget(dialog)
        assert dialog._timed_radio.isChecked()

    def test_duration_spin_range(self, qtbot):
        device = {"id": 1, "name": "PS1", "price_per_hour": 100, "status": "available"}
        dialog = SessionStartDialog(device)
        qtbot.add_widget(dialog)
        assert dialog._duration_spin.minimum() == 1
        assert dialog._duration_spin.maximum() == 480
        assert dialog._duration_spin.value() == 60
        assert dialog._duration_spin.singleStep() == 60

    def test_estimated_price_updates(self, qtbot):
        device = {"id": 1, "name": "PS1", "price_per_hour": 100, "status": "available"}
        dialog = SessionStartDialog(device)
        qtbot.add_widget(dialog)
        dialog._duration_spin.setValue(120)
        expected = "Estimated: 200 MKD"
        assert dialog._timed_price_label.text() == expected

    def test_open_session_duration_zero(self, qtbot):
        device = {"id": 1, "name": "PS1", "price_per_hour": 100, "status": "available"}
        dialog = SessionStartDialog(device)
        qtbot.add_widget(dialog)
        dialog._open_radio.setChecked(True)
        qtbot.mouseClick(dialog._start_button, Qt.MouseButton.LeftButton)
        session_type, duration = dialog.get_session_info()
        assert session_type == "open"
        assert duration == 0

    def test_timed_session_returns_duration(self, qtbot):
        device = {"id": 1, "name": "PS1", "price_per_hour": 100, "status": "available"}
        dialog = SessionStartDialog(device)
        qtbot.add_widget(dialog)
        dialog._duration_spin.setValue(90)
        qtbot.mouseClick(dialog._start_button, Qt.MouseButton.LeftButton)
        session_type, duration = dialog.get_session_info()
        assert session_type == "timed"
        assert duration == 90
