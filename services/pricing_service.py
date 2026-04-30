"""
Pricing service for PlayStation Management System.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class PricingService:
    """Service for calculating session prices."""
    
    @staticmethod
    def calculate_price(price_per_hour: int, minutes: int) -> int:
        """Calculate price based on hourly rate and minutes used.
        
        Uses minute-based billing: rounds up to the next whole minute.
        Price is stored in whole MKD (integer).
        
        Args:
            price_per_hour: Price per hour in MKD
            minutes: Number of minutes used (can be fractional for calculation)
            
        Returns:
            Total price in MKD (integer)
        """
        if minutes <= 0:
            return 0
        
        rounded_minutes = int(minutes)
        if rounded_minutes < minutes:
            rounded_minutes += 1
        
        return (price_per_hour * rounded_minutes) // 60
    
    @staticmethod
    def calculate_estimated_price(price_per_hour: int, duration_minutes: int) -> int:
        """Calculate estimated price for a timed session.
        
        Args:
            price_per_hour: Price per hour in MKD
            duration_minutes: Scheduled duration in minutes
            
        Returns:
            Estimated price in MKD (integer)
        """
        return (price_per_hour * duration_minutes) // 60
    
    @staticmethod
    def calculate_live_price(price_per_hour: int, start_time: str) -> int:
        """Calculate live/estimated price for an ongoing session.
        
        Args:
            price_per_hour: Price per hour in MKD
            start_time: ISO format start time
            
        Returns:
            Current estimated price in MKD (integer)
        """
        start = datetime.fromisoformat(start_time)
        elapsed = datetime.now() - start
        minutes = elapsed.total_seconds() / 60
        return PricingService.calculate_price(price_per_hour, minutes)
    
    @staticmethod
    def calculate_remaining_time(expected_end_time: str) -> int:
        """Calculate remaining minutes until expected end.
        
        Args:
            expected_end_time: ISO format expected end time
            
        Returns:
            Remaining minutes (can be negative if overdue)
        """
        end = datetime.fromisoformat(expected_end_time)
        remaining = end - datetime.now()
        return int(remaining.total_seconds() / 60)
    
    @staticmethod
    def calculate_elapsed_minutes(start_time: str, end_time: Optional[str] = None) -> int:
        """Calculate elapsed minutes since start.
        
        Args:
            start_time: ISO format start time
            end_time: Optional ISO format end time (defaults to now)
            
        Returns:
            Elapsed minutes (rounded up)
        """
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time) if end_time else datetime.now()
        elapsed = end - start
        minutes = elapsed.total_seconds() / 60
        return max(1, int(minutes))
    
    @staticmethod
    def format_price(price: int) -> str:
        """Format price for display.
        
        Args:
            price: Price in MKD
            
        Returns:
            Formatted string like "500 MKD"
        """
        return f"{price} MKD"
    
    @staticmethod
    def format_duration(minutes: int) -> str:
        """Format duration for display.
        
        Args:
            minutes: Duration in minutes
            
        Returns:
            Formatted string like "1h 30m"
        """
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours}h"
        return f"{hours}h {mins}m"
    
    @staticmethod
    def format_time_remaining(minutes: int) -> str:
        """Format remaining time for display.
        
        Args:
            minutes: Remaining minutes (can be negative)
            
        Returns:
            Formatted string like "-5m" or "1h 30m"
        """
        if minutes < 0:
            return f"-{abs(minutes)}m"
        return PricingService.format_duration(minutes)
    
    @staticmethod
    def format_expected_end(expected_end_time: str) -> str:
        """Format expected end time for display.
        
        Args:
            expected_end_time: ISO format expected end time
            
        Returns:
            Formatted time string like "14:30"
        """
        dt = datetime.fromisoformat(expected_end_time)
        return dt.strftime("%H:%M")
    
    @staticmethod
    def calculate_new_expected_end(current_expected_end: str, additional_minutes: int) -> str:
        """Calculate new expected end time when extending a session.
        
        Args:
            current_expected_end: Current expected end time (ISO format)
            additional_minutes: Additional minutes to add
            
        Returns:
            New expected end time (ISO format)
        """
        current = datetime.fromisoformat(current_expected_end)
        new_end = current + timedelta(minutes=additional_minutes)
        return new_end.isoformat()
    
    @staticmethod
    def calculate_billed_minutes(start_time: str, end_time: Optional[str] = None) -> int:
        """Calculate billed minutes (rounded up to whole minutes).
        
        Args:
            start_time: ISO format start time
            end_time: Optional ISO format end time (defaults to now)
            
        Returns:
            Billed minutes (minimum 1)
        """
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time) if end_time else datetime.now()
        elapsed_seconds = (end - start).total_seconds()
        
        minutes = elapsed_seconds / 60
        billed = int(minutes)
        if billed < minutes:
            billed += 1
        
        return max(1, billed)