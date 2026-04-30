"""
Session service for PlayStation Management System.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from db import (
    create_session, get_active_session, get_session, get_all_active_sessions,
    end_session as db_end_session, mark_session_overdue, extend_session as db_extend_session,
    update_device_status, get_device
)
from services.pricing_service import PricingService
from models import Session, Device

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing play sessions."""
    
    @staticmethod
    def get_active_session_for_device(device_id: int) -> Optional[Dict[str, Any]]:
        """Get the active session for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            Active session details or None if no active session
        """
        return get_active_session(device_id)
    
    @staticmethod
    def start_timed_session(device_id: int, duration_minutes: int) -> int:
        """Start a timed session.
        
        Args:
            device_id: Device ID
            duration_minutes: Session duration in minutes
            
        Returns:
            Session ID
            
        Raises:
            ValueError: If device is already in use or not found
        """
        device = get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        if device['status'] == 'in_use':
            raise ValueError("Device is already in use")
        
        expected_end = datetime.now() + timedelta(minutes=duration_minutes)
        
        session_id = create_session(device_id, 'timed', expected_end.isoformat())
        
        return session_id
    
    @staticmethod
    def start_open_session(device_id: int) -> int:
        """Start an open-ended session.
        
        Args:
            device_id: Device ID
            
        Returns:
            Session ID
            
        Raises:
            ValueError: If device is already in use or not found
        """
        device = get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        if device['status'] == 'in_use':
            raise ValueError("Device is already in use")
        
        session_id = create_session(device_id, 'open', None)
        
        return session_id
    
    @staticmethod
    def end_session(session_id: int) -> Dict[str, Any]:
        """End a session and return final details.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with session details including final price
        """
        session = get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        device = get_device(session['device_id'])
        if not device:
            raise ValueError("Device not found")
        
        start_time = session['start_time']
        end_time = datetime.now().isoformat()
        
        billed_minutes = PricingService.calculate_billed_minutes(start_time, end_time)
        
        final_price = PricingService.calculate_price(device['price_per_hour'], billed_minutes)
        
        db_end_session(session_id, final_price, billed_minutes)
        
        session = get_session(session_id)
        
        return {
            'session_id': session_id,
            'device_name': device['name'],
            'session_type': session['session_type'],
            'start_time': session['start_time'],
            'end_time': session['end_time'],
            'duration_minutes': billed_minutes,
            'final_price': final_price,
            'price_per_hour': device['price_per_hour']
        }
    
    @staticmethod
    def extend_session(session_id: int, additional_minutes: int) -> str:
        """Extend a timed session.
        
        Args:
            session_id: Session ID
            additional_minutes: Minutes to add
            
        Returns:
            New expected end time
            
        Raises:
            ValueError: If session not found
        """
        session = get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        if session['session_type'] != 'timed':
            raise ValueError("Cannot extend open-ended session")
        
        current_expected = session['expected_end_time']
        if not current_expected:
            raise ValueError("No expected end time set")
        
        new_expected = PricingService.calculate_new_expected_end(current_expected, additional_minutes)
        
        db_extend_session(session_id, new_expected)
        
        return new_expected
    
    @staticmethod
    def get_session_details(session_id: int) -> Optional[Dict[str, Any]]:
        """Get session details with calculated values.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with session details or None
        """
        session = get_session(session_id)
        if not session:
            return None
        
        device = get_device(session['device_id'])
        if not device:
            return None
        
        details = {
            'id': session['id'],
            'device_id': session['device_id'],
            'device_name': device['name'],
            'session_type': session['session_type'],
            'start_time': session['start_time'],
            'expected_end_time': session['expected_end_time'],
            'status': session['status'],
            'price_per_hour': device['price_per_hour']
        }
        
        if session['session_type'] == 'timed' and session['expected_end_time']:
            remaining = PricingService.calculate_remaining_time(session['expected_end_time'])
            details['remaining_minutes'] = remaining
            details['expected_end_time_formatted'] = PricingService.format_expected_end(session['expected_end_time'])
        
        if session['status'] == 'active' or session['status'] == 'overdue':
            details['elapsed_minutes'] = PricingService.calculate_elapsed_minutes(session['start_time'])
            details['current_price'] = PricingService.calculate_live_price(
                device['price_per_hour'], session['start_time']
            )
        else:
            details['billed_minutes'] = session['billed_minutes']
            details['final_price'] = session['final_price']
        
        return details
    
    @staticmethod
    def get_active_sessions_with_details() -> List[Dict[str, Any]]:
        """Get all active sessions with calculated details.
        
        Returns:
            List of session details
        """
        sessions = get_all_active_sessions()
        result = []
        
        for session in sessions:
            details = SessionService.get_session_details(session['id'])
            if details:
                result.append(details)
        
        return result
    
    @staticmethod
    def check_and_mark_overdue() -> List[int]:
        """Check for expired timed sessions and mark them as overdue.
        
        Returns:
            List of session IDs that were marked as overdue
        """
        active_sessions = get_all_active_sessions()
        now = datetime.now()
        overdue_ids = []
        
        for session in active_sessions:
            if session['session_type'] == 'timed' and session['expected_end_time']:
                expected_end = datetime.fromisoformat(session['expected_end_time'])
                if now >= expected_end and session['status'] == 'active':
                    mark_session_overdue(session['id'])
                    overdue_ids.append(session['id'])
        
        return overdue_ids
    
    @staticmethod
    def recover_active_sessions() -> int:
        """Recover any sessions that were active when app closed.
        
        Returns:
            Number of sessions recovered
        """
        active_sessions = get_all_active_sessions()
        
        recovered = 0
        for session in active_sessions:
            if session['session_type'] == 'timed' and session['expected_end_time']:
                expected_end = datetime.fromisoformat(session['expected_end_time'])
                if datetime.now() >= expected_end and session['status'] == 'active':
                    mark_session_overdue(session['id'])
                    device = get_device(session['device_id'])
                    if device:
                        update_device_status(device['id'], 'in_use')
                else:
                    device = get_device(session['device_id'])
                    if device and device['status'] == 'available':
                        update_device_status(session['device_id'], 'in_use')
            else:
                device = get_device(session['device_id'])
                if device and device['status'] == 'available':
                    update_device_status(session['device_id'], 'in_use')
            recovered += 1
        
        return recovered
    
    @staticmethod
    def acknowledge_alert(session_id: int) -> bool:
        """Acknowledge an overdue session alert.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if acknowledged successfully
        """
        from db import acknowledge_session
        return acknowledge_session(session_id)