"""
Extend session dialog for PlayStation Management System.
"""

import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSpinBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from utils.app_path import get_resource_path
from services import PricingService, SessionService

MIN_EXTENSION_DURATION = 15
MAX_EXTENSION_DURATION = 480
DEFAULT_EXTENSION_DURATION = 30

class ExtendSessionDialog(QDialog):
    def __init__(self, session: dict, parent=None):
        super().__init__(parent)
        self._session = session
        self._setup_ui()
        
        icon_path = get_resource_path("resources/icon.png")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Extend Session")
        self.setMinimumSize(QSize(350, 250))
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        header = QLabel(f"Extend Session - {self._session['device_name']}")
        font = QFont("Arial", 14)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        current_info = QLabel(f"Current end time: {self._session.get('expected_end_time_formatted', 'N/A')}")
        current_info.setFont(QFont("Arial", 12))
        current_info.setStyleSheet("color: #666;")
        current_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(current_info)
        
        layout.addSpacing(20)
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Add time:"))
        
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(MIN_EXTENSION_DURATION, MAX_EXTENSION_DURATION)
        self._duration_spin.setValue(DEFAULT_EXTENSION_DURATION)
        self._duration_spin.setSuffix(" min")
        self._duration_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                font-size: 14px;
            }
        """)
        self._duration_spin.valueChanged.connect(self._on_duration_changed)
        time_layout.addWidget(self._duration_spin)
        
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        self._new_price_label = QLabel()
        self._new_price_label.setFont(QFont("Arial", 12))
        self._new_price_label.setAlignment(Qt.AlignCenter)
        self._new_price_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self._new_price_label)
        
        self._update_new_price()
        
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
        
        extend_btn = QPushButton("Extend Session")
        extend_btn.setMinimumHeight(40)
        extend_btn.setStyleSheet("""
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
        """)
        extend_btn.clicked.connect(self._on_extend_clicked)
        buttons.addWidget(extend_btn)
        
        layout.addLayout(buttons)
    
    def _on_duration_changed(self):
        """Handle duration change."""
        self._update_new_price()
    
    def _update_new_price(self):
        """Update new estimated price display."""
        additional = self._duration_spin.value()
        new_expected = PricingService.calculate_new_expected_end(
            self._session['expected_end_time'], additional
        )
        new_time = PricingService.format_expected_end(new_expected)
        
        rate = self._session.get('price_per_hour', 0)
        additional_price = PricingService.calculate_estimated_price(rate, additional)
        
        current_price = self._session.get('current_price', 0)
        total_price = current_price + additional_price
        
        self._new_price_label.setText(
            f"New end time: {new_time} | Additional: {PricingService.format_price(additional_price)}"
        )
    
    def _on_extend_clicked(self):
        """Handle extend button click."""
        try:
            additional = self._duration_spin.value()
            SessionService.extend_session(self._session['id'], additional)
            self.accept()
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", str(e))