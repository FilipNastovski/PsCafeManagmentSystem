"""
Device management dialog for PlayStation Management System.
"""

import os
import re
from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QFrame,
                             QGridLayout, QLineEdit, QSpinBox, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from utils.app_path import get_resource_path
from db import get_all_devices, create_device, update_device, delete_device
from db import get_next_device_number, device_name_exists

# Device naming constraints
DEVICE_NAME_PATTERN = r'^[a-zA-Z0-9\-_ ]+$'
DEVICE_NAME_MIN_LENGTH = 1
DEVICE_NAME_MAX_LENGTH = 50
MIN_DEVICE_PRICE = 10
MAX_DEVICE_PRICE = 2000
DEFAULT_DEVICE_PRICE = 70

class DeviceCard(QFrame):
    """Individual device card for device manager."""
    
    def __init__(self, device: dict, parent_dialog, parent=None):
        super().__init__(parent)
        self._device = device
        self._parent_dialog = parent_dialog
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the device card UI."""
        self.setMinimumSize(QSize(300, 120))
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            DeviceCard {
                background-color: #263238;
                border: 1px solid #37474f;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        name_layout = QHBoxLayout()
        self._name_label = QLabel(self._device['name'])
        self._name_label.setFont(QFont("Arial", 14))
        self._name_label.setStyleSheet("color: #ffffff;")
        name_layout.addWidget(self._name_label)
        
        name_layout.addStretch()
        
        status_label = QLabel(self._device['status'].upper())
        if self._device['status'] == 'available':
            status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        font = QFont("Arial", 10)
        font.setBold(True)
        status_label.setFont(font)
        name_layout.addWidget(status_label)
        
        layout.addLayout(name_layout)
        
        price_label = QLabel(f"Rate: {self._device['price_per_hour']} MKD/hour")
        price_label.setFont(QFont("Arial", 11))
        price_label.setStyleSheet("color: #B0BEC5;")
        layout.addWidget(price_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setMinimumHeight(35)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        edit_btn.clicked.connect(self._on_edit_clicked)
        button_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.setMinimumHeight(35)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C62828;
            }
        """)
        remove_btn.clicked.connect(self._on_remove_clicked)
        button_layout.addWidget(remove_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        from db import get_active_session
        if get_active_session(self._device['id']):
            QMessageBox.warning(self, "Cannot Edit", "Cannot edit device while a session is active. End the session first.")
            return
        
        dialog = DeviceEditDialog(self._device, self)
        if dialog.exec():
            name = dialog.get_name()
            price = dialog.get_price()
            try:
                update_device(self._device['id'], name, price)
                self._parent_dialog.refresh_devices()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def _on_remove_clicked(self):
        """Handle remove button click."""
        reply = QMessageBox.question(
            self, "Remove Device",
            f"Remove device '{self._device['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if delete_device(self._device['id']):
                    from db import sync_device_sessions
                    sync_device_sessions()
                    self._parent_dialog.refresh_devices()
                else:
                    QMessageBox.warning(
                        self, "Cannot Remove",
                        "Device has an active session. End the session first."
                    )
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))


class DeviceEditDialog(QDialog):
    """Dialog for adding or editing a device."""
    
    def __init__(self, device: dict = None, parent=None):
        super().__init__(parent)
        self._device = device
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        if self._device:
            self.setWindowTitle("Edit Device")
        else:
            self.setWindowTitle("Add Device")
        
        self.setMinimumSize(QSize(350, 250))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_layout.addStretch()
        
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., PS1, PS1-VIP, PS-One")
        self._name_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                min-width: 150px;
            }
        """)
        
        if self._device:
            self._name_edit.setText(self._device['name'])
        else:
            next_num = get_next_device_number()
            self._name_edit.setText(f"PS{next_num}")
        
        name_layout.addWidget(self._name_edit)
        name_layout.addWidget(QLabel("(optional)"))
        layout.addLayout(name_layout)
        
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Price per Hour:"))
        price_layout.addStretch()
        
        self._price_input = QSpinBox()
        self._price_input.setRange(MIN_DEVICE_PRICE, MAX_DEVICE_PRICE)
        self._price_input.setSingleStep(50)
        if self._device:
            self._price_input.setValue(self._device['price_per_hour'])
        else:
            self._price_input.setValue(DEFAULT_DEVICE_PRICE)
        self._price_input.setSuffix(" MKD")
        self._price_input.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 14px;
                min-width: 100px;
            }
        """)
        price_layout.addWidget(self._price_input)
        layout.addLayout(price_layout)
        
        self._warning_label = QLabel("")
        self._warning_label.setFont(QFont("Arial", 9))
        self._warning_label.setStyleSheet("color: #FF5722;")
        self._warning_label.setVisible(False)
        layout.addWidget(self._warning_label)
        
        layout.addStretch()
        
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #546E7A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 24px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        buttons.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 24px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
        """)
        save_btn.clicked.connect(self._validate_and_accept)
        buttons.addWidget(save_btn)
        
        layout.addLayout(buttons)
    
    def get_name(self):
        """Get device name."""
        return self._name_edit.text().strip()
    
    def get_price(self):
        """Get device price."""
        return self._price_input.value()
    
    def _validate_and_accept(self):
        """Validate and save the device."""
        name = self.get_name()
        
        # Validate name is not empty
        if not name:
            self._warning_label.setText("Name cannot be empty")
            self._warning_label.setVisible(True)
            return
        
        # Validate name length
        if len(name) < DEVICE_NAME_MIN_LENGTH or len(name) > DEVICE_NAME_MAX_LENGTH:
            self._warning_label.setText(f"Name must be between {DEVICE_NAME_MIN_LENGTH} and {DEVICE_NAME_MAX_LENGTH} characters")
            self._warning_label.setVisible(True)
            return
        
        # Validate name contains only allowed characters
        if not re.match(DEVICE_NAME_PATTERN, name):
            self._warning_label.setText("Name can only contain letters, numbers, hyphens, underscores, and spaces")
            self._warning_label.setVisible(True)
            return
        
        # Check for duplicate name
        exclude_id = self._device['id'] if self._device else None
        if device_name_exists(name, exclude_id):
            self._warning_label.setText(f"Device '{name}' already exists. Please use a different name.")
            self._warning_label.setVisible(True)
            return
        
        self._warning_label.setVisible(False)
        self.accept()


class DeviceManagerDialog(QDialog):
    """Dialog for managing devices using card layout."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_devices()
        
        icon_path = get_resource_path("resources/icon.png")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Manage Devices")
        self.setMinimumSize(QSize(700, 500))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        font = QFont("Arial", 18)
        font.setBold(True)
        header = QLabel("Devices")
        header.setFont(font)
        header.setStyleSheet("color: #ECEFF1;")
        layout.addWidget(header)
        
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self._device_container = QWidget()
        self._device_grid = QGridLayout(self._device_container)
        self._device_grid.setSpacing(15)
        
        self._scroll.setWidget(self._device_container)
        layout.addWidget(self._scroll)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        add_btn = QPushButton("+ Add Device")
        add_btn.setMinimumHeight(45)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
        """)
        add_btn.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(add_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(45)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #546E7A;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_devices(self):
        """Load devices into cards."""
        while self._device_grid.count():
            item = self._device_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        devices = get_all_devices()
        
        row = 0
        col = 0
        max_cols = 2
        
        for device in devices:
            card = DeviceCard(device, self, self)
            self._device_grid.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        if not devices:
            no_devices = QLabel("No devices configured.\nClick '+ Add Device' to add one.")
            no_devices.setFont(QFont("Arial", 13))
            no_devices.setStyleSheet("color: #78909C; padding: 20px;")
            no_devices.setAlignment(Qt.AlignCenter)
            self._device_grid.addWidget(no_devices, 0, 0, 1, 2)
    
    def _on_add_clicked(self):
        """Handle add button click."""
        dialog = DeviceEditDialog(None, self)
        if dialog.exec():
            name = dialog.get_name()
            price = dialog.get_price()
            try:
                create_device(name, price)
                from db import sync_device_sessions
                sync_device_sessions()
                self._load_devices()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def refresh_devices(self):
        """Refresh the device list."""
        self._load_devices()