import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QGridLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from utils.app_path import get_resource_path
from utils.theme import style
from services import PricingService


class EndSessionDialog(QDialog):
    def __init__(self, session: dict, main_window, parent=None):
        super().__init__(parent)
        self._session = session
        self._main_window = main_window
        self._setup_ui()
        
        icon_path = get_resource_path("resources/icon.png")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
    
    def _setup_ui(self):
        device_name = self._session.get('device_name', 'N/A')
        self.setWindowTitle(f"End Session - {device_name}")
        self.setMinimumSize(QSize(450, 420))
        self.setStyleSheet("QDialog { background-color: palette(window); } QLabel { color: palette(text); }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("Session Summary")
        font = QFont("Arial", 16)
        font.setBold(True)
        header.setFont(font)
        header.setStyleSheet("color: palette(text);")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        summary_box = QFrame()
        summary_box.setStyleSheet("QFrame { background-color: palette(base); border-radius: 8px; border: 1px solid palette(mid); }")
        summary_box.setMinimumHeight(300 if self._session.get('session_type') == 'timed' else 200)

        gl = QGridLayout(summary_box)
        gl.setContentsMargins(15, 15, 15, 15)
        gl.setHorizontalSpacing(15)
        gl.setVerticalSpacing(12)
        
        row = 0
        self._add_row(gl, "Device:", device_name, row)
        row += 1
        
        type_text = "Timed" if self._session.get('session_type') == 'timed' else "Open"
        self._add_row(gl, "Session Type:", type_text, row)
        row += 1
        
        start_time = self._session.get('start_time')
        if start_time and len(start_time) >= 16:
            start_text = start_time[11:16]
        else:
            start_text = 'N/A'
        self._add_row(gl, "Start Time:", start_text, row)
        row += 1
        
        if self._session.get('session_type') == 'timed':
            expected = self._session.get('expected_end_time_formatted', 'N/A')
            self._add_row(gl, "Expected End:", expected, row)
            row += 1
        
        remaining = self._session.get('remaining_minutes')
        if remaining is not None:
            remaining_text = f"{remaining}m" if remaining >= 0 else f"Overdue: {abs(remaining)}m"
            self._add_row(gl, "Remaining:", remaining_text, row)
            row += 1
        
        elapsed = self._session.get('elapsed_minutes')
        if elapsed:
            self._add_row(gl, "Elapsed:", PricingService.format_duration(elapsed), row)
            row += 1
        
        layout.addWidget(summary_box)
        
        price_box = QFrame()
        price_box.setStyleSheet("QFrame { background-color: palette(base); border-radius: 8px; border: 1px solid palette(mid); }")
        price_box.setMinimumHeight(100)
        pl = QGridLayout(price_box)
        pl.setContentsMargins(15, 15, 15, 15)
        pl.setHorizontalSpacing(15)
        pl.setVerticalSpacing(12)
        
        prow = 0
        rate = self._session.get('price_per_hour', 0)
        self._add_row(pl, "Hourly Rate:", PricingService.format_price(rate), prow)
        prow += 1
        
        current = self._session.get('current_price')
        if current:
            self._add_row(pl, "Current:", PricingService.format_price(current), prow)
            prow += 1
        
        layout.addWidget(price_box)
        
        note = QLabel("Price calculated based on actual time used.")
        note.setFont(QFont("Arial", 10))
        note.setStyleSheet(style("text_muted"))
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setStyleSheet("QPushButton { background-color: #546E7A; color: white; border: none; border-radius: 6px; padding: 12px 24px; font-size: 13px; } QPushButton:hover { background-color: #455A64; }")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        if self._session.get('session_type') == 'timed' and self._session.get('remaining_minutes', 0) < 0:
            extend_btn = QPushButton("Extend")
            extend_btn.setMinimumHeight(45)
            extend_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; border: none; border-radius: 6px; padding: 12px 24px; font-size: 13px; } QPushButton:hover { background-color: #F57C00; }")
            extend_btn.clicked.connect(self._on_extend)
            btn_layout.addWidget(extend_btn)
        
        end_btn = QPushButton("End Session")
        end_btn.setMinimumHeight(45)
        end_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; border: none; border-radius: 6px; padding: 12px 24px; font-size: 13px; font-weight: bold; } QPushButton:hover { background-color: #D32F2F; }")
        end_btn.clicked.connect(self.accept)
        btn_layout.addWidget(end_btn)
        
        layout.addLayout(btn_layout)
    
    def _add_row(self, grid, label, value, row):
        l = QLabel(label)
        l.setStyleSheet(style("text_muted", extra="font-size: 12px;"))
        grid.addWidget(l, row, 0)
        
        v = QLabel(str(value))
        v.setStyleSheet(style("text_primary", extra="font-size: 12px; font-weight: bold;"))
        grid.addWidget(v, row, 1)
    
    def _on_extend(self):
        from ui.extend_dialog import ExtendSessionDialog
        dialog = ExtendSessionDialog(self._session, self)
        if dialog.exec():
            self._main_window.refresh_device_cards()
            self.accept()
