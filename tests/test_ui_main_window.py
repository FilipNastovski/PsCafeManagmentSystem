"""UI tests for MainWindow and DeviceCard — uses pytest-qt."""
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

import db
from ui.main_window import MainWindow, DeviceCard


@pytest.fixture(autouse=True)
def setup_test_db(test_db):
    """Ensure the test DB fixture is active for all UI tests."""
    pass


class TestMainWindow:
    def test_empty_device_list_shows_message(self, qtbot):
        window = MainWindow()
        qtbot.add_widget(window)
        grid = window._device_grid
        found_label = False
        for i in range(grid.count()):
            widget = grid.itemAt(i).widget()
            if widget is not None and "No devices" in widget.text():
                found_label = True
                break
        assert found_label

    def test_summary_shows_zero_counts(self, qtbot):
        window = MainWindow()
        qtbot.add_widget(window)
        assert "Total: 0" in window._total_label.text()
        assert "In Use: 0" in window._in_use_label.text()
        assert "Available: 0" in window._available_label.text()

    def test_creates_device_cards(self, qtbot):
        db.create_device("PS1", 100)
        db.create_device("PS2", 150)
        window = MainWindow()
        qtbot.add_widget(window)
        card_count = 0
        for i in range(window._device_grid.count()):
            widget = window._device_grid.itemAt(i).widget()
            if isinstance(widget, DeviceCard):
                card_count += 1
        assert card_count == 2

    def test_summary_shows_correct_counts(self, qtbot):
        db.create_device("PS1", 100)
        db.create_device("PS2", 150)
        window = MainWindow()
        qtbot.add_widget(window)
        assert "Total: 2" in window._total_label.text()
        assert "Available: 2" in window._available_label.text()


class TestDeviceCard:
    def test_available_card_has_start_enabled(self, qtbot):
        device_id = db.create_device("PS1", 100)
        device = db.get_device(device_id)
        window = MainWindow()
        qtbot.add_widget(window)
        card = DeviceCard(device, window)
        qtbot.add_widget(card)
        assert card._start_button.isEnabled()
        assert not card._end_button.isEnabled()

    def test_in_use_card_has_end_enabled(self, qtbot):
        device_id = db.create_device("PS1", 100)
        from datetime import datetime, timedelta
        end_time = (datetime.now() + timedelta(hours=1)).isoformat()
        db.create_session(device_id, "timed", end_time)
        db.update_device_status(device_id, "in_use")
        device = db.get_device(device_id)
        window = MainWindow()
        qtbot.add_widget(window)
        card = DeviceCard(device, window)
        qtbot.add_widget(card)
        assert not card._start_button.isEnabled()
        assert card._end_button.isEnabled()

    def test_mute_button_toggles(self, qtbot):
        from services import AlertService
        from PySide6.QtCore import Qt
        window = MainWindow()
        qtbot.add_widget(window)
        initial = AlertService.is_muted()
        qtbot.mouseClick(window._mute_btn, Qt.MouseButton.LeftButton)
        assert AlertService.is_muted() != initial
