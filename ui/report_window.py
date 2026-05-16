"""
Reports window for PlayStation Management System.
"""

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QFrame,
                             QComboBox, QDateEdit, QGridLayout, QScrollBar)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QFont

from utils.app_path import get_resource_path
from services import ReportService, PricingService
from db import get_all_devices


class SessionCard(QFrame):
    """Individual session card for reports."""
    
    def __init__(self, session: dict, parent=None):
        super().__init__(parent)
        self._session = session
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the session card UI."""
        self.setMinimumSize(QSize(280, 100))
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        status = self._session.get('status', 'completed')
        if status == 'overdue':
            border_color = '#F44336'
        elif status == 'completed':
            border_color = '#4CAF50'
        elif status == 'cancelled':
            border_color = '#FF9800'
        else:
            border_color = '#2196F3'
        
        self.setStyleSheet("""
            SessionCard {
                background-color: #263238;
                border-left: 3px solid """ + border_color + """;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)
        
        header_layout = QHBoxLayout()
        
        device_label = QLabel(self._session.get('device_name', 'Unknown'))
        font = QFont("Arial", 12)
        font.setBold(True)
        device_label.setFont(font)
        device_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(device_label)
        
        header_layout.addStretch()
        
        status_label = QLabel(self._session.get('status', '').upper())
        font = QFont("Arial", 9)
        font.setBold(True)
        status_label.setFont(font)
        status_label.setStyleSheet("color: " + border_color + ";")
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        type_label = QLabel(f"{self._session.get('session_type', 'N/A').capitalize()} Session")
        type_label.setFont(QFont("Arial", 10))
        type_label.setStyleSheet("color: #B0BEC5;")
        layout.addWidget(type_label)
        
        time_layout = QHBoxLayout()
        
        start = self._session.get('start_time', '')[:16].replace('T', ' ')
        if self._session.get('end_time'):
            end = self._session.get('end_time', '')[:16].replace('T', ' ')
            time_label = QLabel(f"{start} - {end}")
        else:
            time_label = QLabel(f"Started: {start}")
        
        time_label.setFont(QFont("Arial", 9))
        time_label.setStyleSheet("color: #90A4AE;")
        time_layout.addWidget(time_label)
        
        time_layout.addStretch()
        
        price_label = QLabel(PricingService.format_price(self._session.get('final_price', 0)))
        font = QFont("Arial", 11)
        font.setBold(True)
        price_label.setFont(font)
        price_label.setStyleSheet("color: #4CAF50;")
        time_layout.addWidget(price_label)
        
        layout.addLayout(time_layout)
        
        duration_label = QLabel(
            f"Duration: {PricingService.format_duration(self._session.get('billed_minutes', 0))}"
        )
        duration_label.setFont(QFont("Arial", 9))
        duration_label.setStyleSheet("color: #78909C;")
        layout.addWidget(duration_label)


class ReportWindow(QMainWindow):
    """Window for viewing reports with card-based layout."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reports")
        self.setMinimumSize(QSize(800, 600))
        
        icon_path = get_resource_path("resources/icon.png")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        
        self._setup_ui()
        self._load_report()
    
    def _setup_ui(self):
        """Setup the UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header = QLabel("Reports")
        font = QFont("Arial", 20)
        font.setBold(True)
        header.setFont(font)
        header.setStyleSheet("color: #ECEFF1;")
        main_layout.addWidget(header)
        
        filters = self._create_filters()
        main_layout.addWidget(filters)
        
        self._summary_frame = self._create_summary()
        main_layout.addWidget(self._summary_frame)
        
        sessions_label = QLabel("Sessions")
        font = QFont("Arial", 14)
        font.setBold(True)
        sessions_label.setFont(font)
        sessions_label.setStyleSheet("color: #B0BEC5;")
        main_layout.addWidget(sessions_label)
        
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #37474f;
                border-radius: 8px;
                background-color: #1E272C;
            }
        """)
        
        self._sessions_container = QWidget()
        self._sessions_grid = QGridLayout(self._sessions_container)
        self._sessions_grid.setSpacing(12)
        
        self._scroll.setWidget(self._sessions_container)
        main_layout.addWidget(self._scroll)
    
    def _create_filters(self) -> QWidget:
        """Create the filter controls."""
        filters = QWidget()
        filters.setStyleSheet("""
            QWidget {
                background-color: #263238;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QHBoxLayout(filters)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Period:"))
        
        self._period_combo = QComboBox()
        self._period_combo.addItems(["Today", "Week", "Month", "Custom"])
        self._period_combo.setMinimumWidth(130)
        self._period_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 12px;
                min-width: 100px;
                background-color: #37474F;
                color: white;
                border: none;
                border-radius: 4px;
            }
        """)
        self._period_combo.currentTextChanged.connect(self._on_period_changed)
        layout.addWidget(self._period_combo)
        
        self._start_date_label = QLabel("From:")
        self._start_date_label.setStyleSheet("color: #B0BEC5;")
        self._start_date_label.setVisible(False)
        layout.addWidget(self._start_date_label)
        
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate())
        self._start_date.setVisible(False)
        self._start_date.setStyleSheet("""
            QDateEdit {
                padding: 6px;
                background-color: #37474F;
                color: white;
                border: none;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._start_date)
        
        self._end_date_label = QLabel("To:")
        self._end_date_label.setStyleSheet("color: #B0BEC5;")
        self._end_date_label.setVisible(False)
        layout.addWidget(self._end_date_label)
        
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        self._end_date.setVisible(False)
        self._end_date.setStyleSheet("""
            QDateEdit {
                padding: 6px;
                background-color: #37474F;
                color: white;
                border: none;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._end_date)
        
        layout.addWidget(QLabel("Device:"))
        
        self._device_combo = QComboBox()
        self._device_combo.addItem("All Devices", 0)
        devices = get_all_devices()
        for device in devices:
            self._device_combo.addItem(device['name'], device['id'])
        self._device_combo.setMinimumWidth(130)
        self._device_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 12px;
                min-width: 100px;
                background-color: #37474F;
                color: white;
                border: none;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._device_combo)
        
        layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(38)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        refresh_btn.clicked.connect(self._load_report)
        layout.addWidget(refresh_btn)
        
        return filters
    
    def _create_summary(self) -> QWidget:
        """Create the summary statistics."""
        summary = QWidget()
        summary.setStyleSheet("""
            QWidget {
                background-color: #263238;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout = QGridLayout(summary)
        layout.setHorizontalSpacing(25)
        layout.setVerticalSpacing(10)
        
        stats = [
            ("Total Sessions", "0", "#4CAF50"),
            ("Total Play Time", "0m", "#2196F3"),
            ("Total Revenue", "0 MKD", "#4CAF50"),
            ("Avg. Duration", "0m", "#FF9800"),
            ("Most Used", "N/A", "#B0BEC5"),
        ]
        
        for i, (label, default_val, color) in enumerate(stats):
            row = i // 3
            col = i % 3
            
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 10))
            lbl.setStyleSheet("color: #78909C;")
            layout.addWidget(lbl, row * 2, col)
            
            if label == "Most Used":
                value_label = QLabel(default_val)
            else:
                value_label = QLabel(default_val)
            font = QFont("Arial", 14)
            font.setBold(True)
            value_label.setFont(font)
            value_label.setStyleSheet("color: " + color + ";")
            layout.addWidget(value_label, row * 2 + 1, col)
        
        self._sessions_label = layout.itemAt(1).widget()
        self._time_label = layout.itemAt(3).widget()
        self._revenue_label = layout.itemAt(5).widget()
        self._avg_label = layout.itemAt(7).widget()
        self._most_used_label = layout.itemAt(9).widget()
        
        return summary
    
    def _on_period_changed(self, period: str):
        """Handle period change."""
        is_custom = period == "Custom"
        self._start_date_label.setVisible(is_custom)
        self._start_date.setVisible(is_custom)
        self._end_date_label.setVisible(is_custom)
        self._end_date.setVisible(is_custom)
    
    def _load_report(self):
        """Load the report data."""
        period = self._period_combo.currentText().lower()
        
        start_date = None
        end_date = None
        if period == "custom":
            start_date = self._start_date.date().toString("yyyy-MM-dd")
            end_date = self._end_date.date().toString("yyyy-MM-dd")
        
        device_id = self._device_combo.currentData()
        
        report = ReportService.generate_report(
            period, device_id=device_id,
            start_date=start_date, end_date=end_date
        )
        
        summary = report['summary']
        self._sessions_label.setText(str(summary['total_sessions']))
        self._time_label.setText(PricingService.format_duration(summary['total_minutes']))
        self._revenue_label.setText(PricingService.format_price(summary['total_revenue']))
        self._avg_label.setText(PricingService.format_duration(summary['average_duration']))
        self._most_used_label.setText(summary['most_used_device'] or "N/A")
        
        sessions = report['sessions']
        
        while self._sessions_grid.count():
            item = self._sessions_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        row = 0
        col = 0
        max_cols = 2
        
        for session in sessions:
            card = SessionCard(session, self)
            self._sessions_grid.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        if not sessions:
            no_sessions = QLabel("No sessions found for this period.")
            no_sessions.setFont(QFont("Arial", 12))
            no_sessions.setStyleSheet("color: #78909C; padding: 20px;")
            no_sessions.setAlignment(Qt.AlignCenter)
            self._sessions_grid.addWidget(no_sessions, 0, 0, 1, 2)