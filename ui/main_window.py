"""
Main window for PlayStation Management System.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QPushButton, QMessageBox,
                             QScrollArea, QFrame, QDialog, QGroupBox)
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QFont, QIcon, QColor

import os
import logging
import traceback
from datetime import datetime
from typing import Dict, Any

from utils.app_path import get_resource_path
from utils.theme import get_theme_colors, style

logger = logging.getLogger(__name__)

from db import get_all_devices, get_device, init_database
from services import SessionService, PricingService, AlertService, ReportService

class DeviceCard(QFrame):
    """Widget representing a single device card."""
    
    def __init__(self, device: Dict[str, Any], main_window, parent=None):
        super().__init__(parent)
        self._device = device
        self._main_window = main_window
        self._session = None
        self._setup_ui()
        self._update_from_device()
    
    def _setup_ui(self):
        """Set up the UI components."""
        self.setMinimumSize(QSize(200, 180)) # 200, 180
        self.setMaximumSize(QSize(500, 240)) # 250, 240
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            DeviceCard {
                background-color: palette(base);
                border: 2px solid palette(mid);
                border-radius: 8px;
            }
            DeviceCard[status="available"] {
                border-left: 5px solid #4CAF50;
            }
            DeviceCard[status="in_use"] {
                border-left: 5px solid #2196F3;
            }
            DeviceCard[status="overdue"] {
                border-left: 5px solid #f44336;
            }
            DeviceCard[status="disabled"] {
                border-left: 5px solid #9e9e9e;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        self._name_label = QLabel(self._device['name'])
        font = QFont("Arial", 14)
        font.setBold(True)
        self._name_label.setFont(font)
        self._name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._name_label)
        
        self._status_label = QLabel("Available")
        self._status_label.setFont(QFont("Arial", 12))
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self._status_label)
        
        self._time_label = QLabel("")
        self._time_label.setFont(QFont("Arial", 11))
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet(style("text_muted"))
        layout.addWidget(self._time_label)
        
        self._price_label = QLabel("")
        self._price_label.setFont(QFont("Arial", 11))
        self._price_label.setAlignment(Qt.AlignCenter)
        self._price_label.setStyleSheet(style("text_muted"))
        layout.addWidget(self._price_label)
        
        self._button_layout = QHBoxLayout()
        self._button_layout.setSpacing(10)
        
        self._start_button = QPushButton("Start")
        self._start_button.setMinimumHeight(40)
        self._start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: palette(button);
                color: palette(text);
            }
        """)
        self._start_button.clicked.connect(self._on_start_clicked)
        self._button_layout.addWidget(self._start_button)
        
        self._end_button = QPushButton("End")
        self._end_button.setMinimumHeight(40)
        self._end_button.setEnabled(False)
        self._end_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: palette(button);
                color: palette(text);
            }
        """)
        self._end_button.clicked.connect(self._on_end_clicked)
        self._button_layout.addWidget(self._end_button)
        
        self._extend_button = QPushButton("Extend")
        self._extend_button.setMinimumHeight(40)
        self._extend_button.setVisible(False)
        self._extend_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:disabled {
                background-color: palette(button);
                color: palette(text);
            }
        """)
        self._extend_button.clicked.connect(self._on_extend_clicked)
        self._button_layout.addWidget(self._extend_button)
        
        layout.addLayout(self._button_layout)
        
        self._overdue_label = QLabel("OVERDUE!")
        font = QFont("Arial", 10)
        font.setBold(True)
        self._overdue_label.setFont(font)
        self._overdue_label.setAlignment(Qt.AlignCenter)
        self._overdue_label.setStyleSheet("color: #f44336; padding: 4px; border-radius: 4px;")
        self._overdue_label.setVisible(False)
        layout.addWidget(self._overdue_label)
    
    def _on_start_clicked(self):
        """Handle start button click."""
        from ui.session_dialog import SessionStartDialog
        dialog = SessionStartDialog(self._device, self)
        if dialog.exec():
            try:
                session_type, duration = dialog.get_session_info()
                if session_type == 'timed':
                    SessionService.start_timed_session(self._device['id'], duration)
                else:
                    SessionService.start_open_session(self._device['id'])
                from db import sync_device_sessions
                sync_device_sessions()
                self._main_window.refresh_device_cards()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to start session: {e}")
    
    def _on_end_clicked(self):
        """Handle end button click."""
        from ui.end_session_dialog import EndSessionDialog
        
        if not self._session or 'id' not in self._session:
            logger.warning(f"End session clicked but no active session found for device {self._device['id']}")
            QMessageBox.warning(self, "Error", "No active session found")
            return
        
        session = SessionService.get_session_details(self._session['id'])
        if not session:
            logger.warning(f"Could not load session details for session {self._session['id']}")
            QMessageBox.warning(self, "Error", "Could not load session details")
            return
        
        dialog = EndSessionDialog(session, self)
        if dialog.exec():
            try:
                session_id = self._session['id']
                logger.info(f"Ending session {session_id}")
                result = SessionService.end_session(session_id)
                logger.info(f"Session {session_id} end result: {result}")
                from db import sync_device_sessions
                sync_device_sessions()
                self._main_window.refresh_device_cards()
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"Failed to end session: {e}\n{error_trace}")
                QMessageBox.critical(self, "Error", f"Failed to end session:\n{e}")
    
    def _on_extend_clicked(self):
        """Handle extend button click."""
        from ui.extend_dialog import ExtendSessionDialog
        
        if not self._session or 'id' not in self._session:
            logger.warning(f"Extend session clicked but no active session found for device {self._device['id']}")
            QMessageBox.warning(self, "Error", "No active session found")
            return
        
        session = SessionService.get_session_details(self._session['id'])
        if not session:
            logger.warning(f"Could not load session details for session {self._session['id']}")
            QMessageBox.warning(self, "Error", "Could not load session details")
            return
        
        dialog = ExtendSessionDialog(session, self)
        if dialog.exec():
            try:
                from db import sync_device_sessions
                sync_device_sessions()
                self._main_window.refresh_device_cards()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to extend session:\n{e}")
    
    def _update_from_device(self):
        """Update card from device data."""
        status = self._device.get('status', 'available')
        self.setProperty("status", status)
        self.style().unpolish(self)
        self.style().polish(self)
        
        colors = get_theme_colors()
        
        if status == 'available':
            self._status_label.setText("Available")
            self._status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self._start_button.setEnabled(True)
            self._end_button.setEnabled(False)
            self._extend_button.setVisible(False)
            self._time_label.setText("")
            self._price_label.setText("")
            self._overdue_label.setVisible(False)
            self._session = None
        elif status == 'in_use':
            active_session = SessionService.get_active_session_for_device(self._device['id'])
            if active_session:
                self._session = SessionService.get_session_details(active_session['id'])
            else:
                self._session = None
            
            if self._session:
                if self._session['session_type'] == 'timed':
                    self._status_label.setText("In Use (Timed)")
                    self._status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
                    remaining = self._session.get('remaining_minutes', 0)
                    if remaining <= 0:
                        self._status_label.setText("Overdue!")
                        self._status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                        self._overdue_label.setVisible(True)
                        self._overdue_label.setStyleSheet(f"color: #f44336; background-color: {colors.bg_overdue_badge}; padding: 4px; border-radius: 4px;")
                        self._extend_button.setVisible(True)
                    else:
                        self._extend_button.setVisible(False)
                    self._time_label.setText(f"Remaining: {PricingService.format_time_remaining(remaining)} | End: {self._session.get('expected_end_time_formatted', '')}")
                else:
                    self._status_label.setText("In Use (Open)")
                    self._status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
                    self._extend_button.setVisible(False)
                    elapsed = self._session.get('elapsed_minutes', 0)
                    self._time_label.setText(f"Elapsed: {PricingService.format_duration(elapsed)}")
                
                current_price = self._session.get('current_price', 0)
                self._price_label.setText(f"Current: {PricingService.format_price(current_price)}")

            self._start_button.setEnabled(False)
            self._end_button.setEnabled(True)
            if self._session and self._session.get('session_type') == 'timed':
                self._extend_button.setVisible(self._session.get('remaining_minutes', 0) <= 0)
            else:
                self._extend_button.setVisible(False)
        else:
            self._status_label.setText("Disabled")
            self._status_label.setStyleSheet("color: #9e9e9e;")
            self._start_button.setEnabled(False)
            self._end_button.setEnabled(False)
            self._extend_button.setVisible(False)
    
    def update_session_state(self):
        """Update session state (called by timer)."""
        if self._session and self._device.get('status') in ('in_use', 'overdue'):
            self._session = SessionService.get_session_details(self._session['id'])
            if self._session:
                if self._session['session_type'] == 'timed':
                    remaining = self._session.get('remaining_minutes', 0)
                    self._time_label.setText(f"Remaining: {PricingService.format_time_remaining(remaining)} | End: {self._session.get('expected_end_time_formatted', '')}")
                    if remaining <= 0 and self._status_label.text() != "Overdue!":
                        self._status_label.setText("Overdue!")
                        self._status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                        self._overdue_label.setVisible(True)
                        colors = get_theme_colors()
                        self._overdue_label.setStyleSheet(f"color: #f44336; background-color: {colors.bg_overdue_badge}; padding: 4px; border-radius: 4px;")
                        self._extend_button.setVisible(True)
                    elif remaining > 0:
                        self._extend_button.setVisible(False)
                else:
                    self._extend_button.setVisible(False)
                    elapsed = self._session.get('elapsed_minutes', 0)
                    self._time_label.setText(f"Elapsed: {PricingService.format_duration(elapsed)}")
                
                current_price = self._session.get('current_price', 0)
                self._price_label.setText(f"Current: {PricingService.format_price(current_price)}")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlayStation Management")
        self.setMinimumSize(QSize(900, 600))
        
        icon_path = get_resource_path("resources/icon.png")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        
        init_database()
        
        from db import sync_device_sessions
        sync_device_sessions()
        
        SessionService.recover_active_sessions()
        
        self._setup_ui()
        self._setup_timer()
        self._check_alerts()
    
    def _setup_ui(self):
        """Set up the main UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        header = self._create_header()
        main_layout.addWidget(header)
        
        self._summary = self._create_summary()
        main_layout.addWidget(self._summary)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self._device_container = QWidget()
        self._device_grid = QGridLayout(self._device_container)
        self._device_grid.setSpacing(15)
        
        scroll.setWidget(self._device_container)
        main_layout.addWidget(scroll)
        
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        self._credits_label = QLabel("PsManagementSystem V-0.1 Filip Nastovski")
        self._credits_label.setFont(QFont("Arial", 9))
        self._credits_label.setStyleSheet(style("text_credits"))
        bottom_layout.addWidget(self._credits_label)
        bottom_layout.addStretch()
        self._mute_btn = QPushButton("🔊")
        self._mute_btn.setFixedSize(30, 25)
        self._mute_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: palette(mid);
                border-radius: 3px;
            }
        """)
        self._mute_btn.clicked.connect(self._on_mute_clicked)
        bottom_layout.addWidget(self._mute_btn)
        main_layout.addWidget(bottom)
        
        self._create_device_cards()
    
    def _create_header(self) -> QWidget:
        """Create the header with title and buttons."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("PlayStation Management")
        font = QFont("Arial", 20)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        layout.addStretch()
        
        self._device_manage_btn = QPushButton("Manage Devices")
        self._device_manage_btn.setMinimumHeight(40)
        self._device_manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #607d8b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #546e7a;
            }
        """)
        self._device_manage_btn.clicked.connect(self._show_device_manager)
        layout.addWidget(self._device_manage_btn)
        
        self._reports_btn = QPushButton("Reports")
        self._reports_btn.setMinimumHeight(40)
        self._reports_btn.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
        """)
        self._reports_btn.clicked.connect(self._show_reports)
        layout.addWidget(self._reports_btn)
        
        return header
    
    def _create_summary(self) -> QWidget:
        """Create the summary statistics bar."""
        summary = QWidget()
        summary.setStyleSheet("""
            QWidget {
                background-color: #e3f2fd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout = QHBoxLayout(summary)
        layout.setContentsMargins(20, 15, 20, 15)
        
        devices = get_all_devices()
        total = len(devices)
        in_use = sum(1 for d in devices if d['status'] == 'in_use')
        available = sum(1 for d in devices if d['status'] == 'available')
        
        self._total_label = QLabel(f"Total: {total}")
        font = QFont("Arial", 14)
        font.setBold(True)
        self._total_label.setFont(font)
        self._total_label.setStyleSheet("color: #1976D2;")
        layout.addWidget(self._total_label)
        
        layout.addSpacing(30)
        
        self._in_use_label = QLabel(f"In Use: {in_use}")
        font2 = QFont("Arial", 14)
        font2.setBold(True)
        self._in_use_label.setFont(font2)
        self._in_use_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(self._in_use_label)
        
        layout.addSpacing(30)
        
        self._available_label = QLabel(f"Available: {available}")
        font3 = QFont("Arial", 14)
        font3.setBold(True)
        self._available_label.setFont(font3)
        self._available_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(self._available_label)
        
        layout.addStretch()
        
        self._refresh_label = QLabel(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        self._refresh_label.setFont(QFont("Arial", 10))
        self._refresh_label.setStyleSheet(style("text_muted"))
        layout.addWidget(self._refresh_label)
        
        return summary
    
    def _create_device_cards(self):
        """Create device cards."""
        while self._device_grid.count():
            item = self._device_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        devices = get_all_devices()
        
        row = 0
        col = 0
        for device in devices:
            card = DeviceCard(device, self)
            self._device_grid.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        if not devices:
            no_devices = QLabel("No devices configured. Click 'Manage Devices' to add devices.")
            no_devices.setFont(QFont("Arial", 14))
            no_devices.setStyleSheet(style("text_muted", extra="padding: 20px;"))
            no_devices.setAlignment(Qt.AlignCenter)
            self._device_grid.addWidget(no_devices, 0, 0, 1, 4)
    
    def _on_mute_clicked(self):
        """Handle mute button click."""
        from services import AlertService
        AlertService.toggle_mute()
        if AlertService.is_muted():
            self._mute_btn.setText("🔇")
        else:
            self._mute_btn.setText("🔊")
    
    def _setup_timer(self):
        """Set up the refresh timer."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(1000)
    
    def _on_timer_tick(self):
        """Handle timer tick - update display."""
        self._check_alerts()
        
        devices = get_all_devices()
        total = len(devices)
        in_use = sum(1 for d in devices if d['status'] == 'in_use')
        available = sum(1 for d in devices if d['status'] == 'available')
        
        self._total_label.setText(f"Total: {total}")
        self._in_use_label.setText(f"In Use: {in_use}")
        self._available_label.setText(f"Available: {available}")
        
        for i in range(self._device_grid.count()):
            widget = self._device_grid.itemAt(i).widget()
            if isinstance(widget, DeviceCard):
                widget.update_session_state()
        
        self._refresh_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def _check_alerts(self):
        """Check for session time expiration."""
        overdue_ids = SessionService.check_and_mark_overdue()
        
        if overdue_ids:
            from db import sync_device_sessions
            sync_device_sessions()
            alert_service = AlertService()
            for session_id in overdue_ids:
                session = SessionService.get_session_details(session_id)
                if session and not session.get('acknowledged'):
                    alert_service.play_alert()
                    break
    
    def _show_device_manager(self):
        """Show the device management window."""
        from ui.device_dialog import DeviceManagerDialog
        dialog = DeviceManagerDialog(self)
        dialog.exec()
        self._create_device_cards()
    
    def _show_reports(self):
        """Show the reports window."""
        from ui.report_window import ReportWindow
        window = ReportWindow(self)
        window.show()
    
    def refresh_device_cards(self):
        """Refresh device cards (called after session changes)."""
        self._create_device_cards()
    
    def closeEvent(self, event):
        """Handle window close."""
        logger.info("Closing main window")
        if hasattr(self, '_timer'):
            self._timer.stop()
        
        # Close database connection
        try:
            from db import close_connection
            close_connection()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        
        event.accept()