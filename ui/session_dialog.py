"""
Session start dialog for PlayStation Management System.
Allows choosing between timed and open sessions.
"""

import os
from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSpinBox, QRadioButton,
                             QGroupBox, QMessageBox, QGridLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from services import PricingService, SessionService
from db import get_device

MIN_SESSION_DURATION = 1
MAX_SESSION_DURATION = 480
DEFAULT_SESSION_DURATION = 60

class SessionStartDialog(QDialog):
    def __init__(self, device: dict, parent=None):
        super().__init__(parent)
        self._device = device
        self._session_type = None
        self._duration = 0
        self._setup_ui()
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icon.png")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle(f"Start Session - {self._device['name']}")
        self.setMinimumSize(QSize(400, 350))
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        device_info = QLabel(f"Device: {self._device['name']}")
        font = QFont("Arial", 14)
        font.setBold(True)
        device_info.setFont(font)
        layout.addWidget(device_info)
        
        price_info = QLabel(f"Rate: {PricingService.format_price(self._device['price_per_hour'])}/hour")
        price_info.setFont(QFont("Arial", 12))
        price_info.setStyleSheet("color: #666;")
        layout.addWidget(price_info)
        
        layout.addSpacing(10)
        
        self._timed_radio = QRadioButton("Timed Session")
        font = QFont("Arial", 12)
        font.setBold(True)
        self._timed_radio.setFont(font)
        self._timed_radio.setChecked(True)
        self._timed_radio.toggled.connect(self._on_type_toggled)
        layout.addWidget(self._timed_radio)
        
        timed_options = QWidget()
        timed_layout = QHBoxLayout(timed_options)
        timed_layout.setContentsMargins(20, 0, 0, 0)
        
        timed_layout.addWidget(QLabel("Duration:"))
        
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(MIN_SESSION_DURATION, MAX_SESSION_DURATION)
        self._duration_spin.setValue(DEFAULT_SESSION_DURATION)
        self._duration_spin.setSingleStep(60)
        self._duration_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                font-size: 12px;
            }
        """)
        self._duration_spin.valueChanged.connect(self._on_duration_changed)
        timed_layout.addWidget(self._duration_spin)
        timed_layout.addWidget(QLabel(" min"))
        
        self._timed_price_label = QLabel()
        self._timed_price_label.setFont(QFont("Arial", 11))
        self._timed_price_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        timed_layout.addWidget(self._timed_price_label)
        
        timed_layout.addStretch()
        layout.addWidget(timed_options)
        
        layout.addSpacing(10)
        
        self._open_radio = QRadioButton("Open Session")
        font = QFont("Arial", 12)
        font.setBold(True)
        self._open_radio.setFont(font)
        self._open_radio.toggled.connect(self._on_type_toggled)
        layout.addWidget(self._open_radio)
        
        open_options = QWidget()
        open_layout = QVBoxLayout(open_options)
        open_layout.setContentsMargins(20, 0, 0, 0)
        
        open_info = QLabel("Session stays active until manually ended.")
        open_info.setFont(QFont("Arial", 10))
        open_info.setStyleSheet("color: #666;")
        open_layout.addWidget(open_info)
        
        open_price_info = QLabel("Price: Live calculation based on actual time used")
        open_price_info.setFont(QFont("Arial", 10))
        open_price_info.setStyleSheet("color: #666;")
        open_layout.addWidget(open_price_info)
        
        layout.addWidget(open_options)
        
        self._update_timed_price()
        
        layout.addStretch()
        
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        self._start_button = QPushButton("Start Session")
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
        """)
        self._start_button.clicked.connect(self._on_start_clicked)
        buttons.addWidget(self._start_button)
        
        layout.addLayout(buttons)
    
    def _on_type_toggled(self):
        """Handle session type toggle."""
        if self._timed_radio.isChecked():
            self._duration_spin.setEnabled(True)
            self._session_type = 'timed'
        else:
            self._duration_spin.setEnabled(True)
            self._session_type = 'open'
    
    def _on_duration_changed(self):
        """Handle duration change."""
        self._update_timed_price()
    
    def _update_timed_price(self):
        """Update estimated price display."""
        duration = self._duration_spin.value()
        price = PricingService.calculate_estimated_price(self._device['price_per_hour'], duration)
        self._timed_price_label.setText(f"Estimated: {PricingService.format_price(price)}")
    
    def _on_start_clicked(self):
        """Handle start button click."""
        if self._timed_radio.isChecked():
            self._session_type = 'timed'
            self._duration = self._duration_spin.value()
        else:
            self._session_type = 'open'
            self._duration = 0
        
        self.accept()
    
    def get_session_info(self):
        """Get the session information."""
        return self._session_type, self._duration