"""
Data models for PlayStation Management System.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class DeviceStatus(Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    OVERDUE = "overdue"
    DISABLED = "disabled"

class SessionType(Enum):
    TIMED = "timed"
    OPEN = "open"

class SessionStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

@dataclass
class Device:
    id: int
    name: str
    price_per_hour: int
    status: str = "available"
    created_at: Optional[str] = None
    is_disabled: bool = False

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'price_per_hour': self.price_per_hour,
            'status': self.status,
            'created_at': self.created_at,
            'is_disabled': self.is_disabled
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Device':
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            price_per_hour=data.get('price_per_hour'),
            status=data.get('status', 'available'),
            created_at=data.get('created_at'),
            is_disabled=bool(data.get('is_disabled', 0))
        )

@dataclass
class Session:
    id: int
    device_id: int
    session_type: str
    start_time: str
    expected_end_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str = "active"
    billed_minutes: int = 0
    final_price: int = 0
    acknowledged: bool = False
    device_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'device_id': self.device_id,
            'session_type': self.session_type,
            'start_time': self.start_time,
            'expected_end_time': self.expected_end_time,
            'end_time': self.end_time,
            'status': self.status,
            'billed_minutes': self.billed_minutes,
            'final_price': self.final_price,
            'acknowledged': bool(self.acknowledged),
            'device_name': self.device_name
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        return cls(
            id=data.get('id'),
            device_id=data.get('device_id'),
            session_type=data.get('session_type'),
            start_time=data.get('start_time'),
            expected_end_time=data.get('expected_end_time'),
            end_time=data.get('end_time'),
            status=data.get('status', 'active'),
            billed_minutes=data.get('billed_minutes', 0),
            final_price=data.get('final_price', 0),
            acknowledged=bool(data.get('acknowledged', 0)),
            device_name=data.get('device_name')
        )

    def is_timed(self) -> bool:
        return self.session_type == 'timed'

    def is_open(self) -> bool:
        return self.session_type == 'open'

    def is_active(self) -> bool:
        return self.status in ('active', 'overdue')

    def is_completed(self) -> bool:
        return self.status == 'completed'

    def is_overdue(self) -> bool:
        return self.status == 'overdue'