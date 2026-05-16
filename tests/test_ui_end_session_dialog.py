"""UI tests for EndSessionDialog — uses pytest-qt."""
import pytest
from PySide6.QtWidgets import QApplication, QLabel

from ui.end_session_dialog import EndSessionDialog


@pytest.fixture(autouse=True)
def setup_test_db(test_db):
    pass


class TestEndSessionDialog:
    def _make_session(self, **overrides):
        base = {
            "id": 1, "device_id": 1, "device_name": "PS1",
            "session_type": "timed", "start_time": "2026-05-16T10:00:00",
            "expected_end_time": "2026-05-16T11:00:00",
            "expected_end_time_formatted": "11:00",
            "remaining_minutes": 30, "elapsed_minutes": 30,
            "current_price": 50, "price_per_hour": 100,
            "status": "active",
        }
        base.update(overrides)
        return base

    def test_shows_device_name_in_title(self, qtbot):
        session = self._make_session()
        dialog = EndSessionDialog(session, None)
        qtbot.add_widget(dialog)
        assert "PS1" in dialog.windowTitle()

    def test_shows_session_summary(self, qtbot):
        session = self._make_session()
        dialog = EndSessionDialog(session, None)
        qtbot.add_widget(dialog)
        labels = dialog.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]
        assert any("PS1" in t for t in texts)
        assert any("Timed" in t for t in texts)

    def test_shows_hourly_rate(self, qtbot):
        session = self._make_session()
        dialog = EndSessionDialog(session, None)
        qtbot.add_widget(dialog)
        labels = dialog.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]
        assert any("100 MKD" in t for t in texts)

    def test_accept_on_end_session(self, qtbot):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QPushButton
        session = self._make_session()
        dialog = EndSessionDialog(session, None)
        qtbot.add_widget(dialog)
        buttons = dialog.findChildren(QPushButton)
        end_btn = None
        for btn in buttons:
            if btn.text() == "End Session":
                end_btn = btn
                break
        assert end_btn is not None
        qtbot.mouseClick(end_btn, Qt.MouseButton.LeftButton)
        assert dialog.result() == 1
