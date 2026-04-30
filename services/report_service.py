"""
Report service for PlayStation Management System.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from db import get_session_history, get_report_summary, get_all_devices

logger = logging.getLogger(__name__)

class ReportService:
    """Service for generating reports."""
    
    @staticmethod
    def get_date_range(period: str) -> tuple:
        """Get date range for a period.
        
        Args:
            period: 'today', 'week', 'month', or 'custom'
            
        Returns:
            Tuple of (start_date, end_date) in ISO format
        """
        now = datetime.now()
        
        if period == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return (start.isoformat(), end.isoformat())
        
        elif period == 'week':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return (start.isoformat(), end.isoformat())
        
        elif period == 'month':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return (start.isoformat(), end.isoformat())
        
        else:
            return (now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                    now.isoformat())
    
    @staticmethod
    def generate_report(period: str, device_id: Optional[int] = None,
                        session_type: Optional[str] = None,
                        status_filter: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate a report for the specified period.
        
        Args:
            period: 'today', 'week', 'month', or 'custom'
            device_id: Optional device filter
            session_type: Optional session type filter ('timed' or 'open')
            status_filter: Optional status filter ('completed', 'overdue', 'cancelled')
            start_date: Custom start date (ISO format) - used with period='custom'
            end_date: Custom end date (ISO format) - used with period='custom'
            
        Returns:
            Dictionary with report data
        """
        if period == 'custom' and start_date and end_date:
            date_start = start_date
            date_end = end_date
        else:
            date_start, date_end = ReportService.get_date_range(period)
        
        logger.info(f"Generating report: period={period}, device_id={device_id}, session_type={session_type}, status={status_filter}")
        
        summary = get_report_summary(date_start, date_end, device_id)
        
        sessions = get_session_history(
            start_date=date_start,
            end_date=date_end,
            device_id=device_id,
            session_type=session_type,
            status_filter=status_filter
        )
        
        devices = get_all_devices()
        
        return {
            'period': period,
            'start_date': date_start,
            'end_date': date_end,
            'summary': {
                'total_sessions': summary['total_sessions'],
                'total_minutes': summary['total_minutes'],
                'total_revenue': summary['total_revenue'],
                'average_duration': int(summary['avg_duration']) if summary['avg_duration'] else 0,
                'most_used_device': summary['most_used_device']
            },
            'sessions': sessions,
            'devices': devices,
            'filters': {
                'device_id': device_id,
                'session_type': session_type,
                'status_filter': status_filter
            }
        }
    
    @staticmethod
    def format_report_for_display(report: Dict[str, Any]) -> str:
        """Format report data for display.
        
        Args:
            report: Report dictionary
            
        Returns:
            Formatted string
        """
        from services.pricing_service import PricingService
        
        summary = report['summary']
        
        lines = [
            f"Report: {report['period'].upper()}",
            f"Period: {report['start_date'][:10]} to {report['end_date'][:10]}",
            "",
            "Summary:",
            f"  Total Sessions: {summary['total_sessions']}",
            f"  Total Play Time: {PricingService.format_duration(summary['total_minutes'])}",
            f"  Total Revenue: {PricingService.format_price(summary['total_revenue'])}",
            f"  Average Session: {PricingService.format_duration(summary['average_duration'])}",
            f"  Most Used Device: {summary['most_used_device'] or 'N/A'}",
            "",
            f"Sessions: {len(report['sessions'])}"
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def get_device_report(device_id: int, period: str = 'today') -> Dict[str, Any]:
        """Get a report for a specific device.
        
        Args:
            device_id: Device ID
            period: Report period
            
        Returns:
            Device-specific report
        """
        return ReportService.generate_report(period, device_id=device_id)
    
    @staticmethod
    def get_period_options() -> List[Dict[str, str]]:
        """Get available period options.
        
        Returns:
            List of period options
        """
        return [
            {'value': 'today', 'label': 'Today'},
            {'value': 'week', 'label': 'This Week'},
            {'value': 'month', 'label': 'This Month'},
            {'value': 'custom', 'label': 'Custom'}
        ]