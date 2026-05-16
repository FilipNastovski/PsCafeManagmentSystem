"""Integration tests for ReportService — uses isolated test DB fixture."""
import pytest
from datetime import datetime, timedelta

import db
from services.report_service import ReportService


class TestGetDateRange:
    def test_today(self):
        start, end = ReportService.get_date_range("today")
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        now = datetime.now()
        assert start_dt.date() == now.date()
        assert start_dt.hour == 0
        assert end_dt.hour == 23

    def test_week(self):
        start, end = ReportService.get_date_range("week")
        start_dt = datetime.fromisoformat(start)
        now = datetime.now()
        assert start_dt <= now
        assert start_dt.weekday() == 0

    def test_month(self):
        start, end = ReportService.get_date_range("month")
        start_dt = datetime.fromisoformat(start)
        now = datetime.now()
        assert start_dt.day == 1
        assert start_dt.month == now.month

    def test_custom_fallback(self):
        start, end = ReportService.get_date_range("custom")
        start_dt = datetime.fromisoformat(start)
        assert start_dt.hour == 0


class TestGenerateReport:
    def test_empty_report(self, test_db):
        report = ReportService.generate_report("today")
        assert report["summary"]["total_sessions"] == 0
        assert report["summary"]["total_revenue"] == 0
        assert report["sessions"] == []

    def test_report_with_completed_session(self, test_db):
        device_id = db.create_device("PS1", 100)
        session_id = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(session_id, 100, 60)
        report = ReportService.generate_report("custom",
            start_date=(datetime.now() - timedelta(days=1)).isoformat(),
            end_date=(datetime.now() + timedelta(days=1)).isoformat(),
        )
        assert report["summary"]["total_sessions"] == 1
        assert report["summary"]["total_minutes"] == 60
        assert report["summary"]["total_revenue"] == 100
        assert len(report["sessions"]) == 1

    def test_report_filter_by_device(self, test_db):
        d1 = db.create_device("PS1", 100)
        d2 = db.create_device("PS2", 150)
        s1 = db.create_session(d1, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        s2 = db.create_session(d2, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(s1, 100, 60)
        db.end_session(s2, 150, 60)
        report = ReportService.generate_report("custom",
            device_id=d1,
            start_date=(datetime.now() - timedelta(days=1)).isoformat(),
            end_date=(datetime.now() + timedelta(days=1)).isoformat(),
        )
        assert report["summary"]["total_sessions"] == 1
        assert report["sessions"][0]["device_name"] == "PS1"

    def test_report_filter_by_session_type(self, test_db):
        device_id = db.create_device("PS1", 100)
        s1 = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        s2 = db.create_session(device_id, "open", None)
        db.end_session(s1, 100, 60)
        db.end_session(s2, 100, 30)
        report = ReportService.generate_report("custom",
            session_type="open",
            start_date=(datetime.now() - timedelta(days=1)).isoformat(),
            end_date=(datetime.now() + timedelta(days=1)).isoformat(),
        )
        # Summary aggregates all completed sessions; session list is filtered
        assert len(report["sessions"]) == 1
        assert report["sessions"][0]["session_type"] == "open"

    def test_report_filter_by_status(self, test_db):
        device_id = db.create_device("PS1", 100)
        s1 = db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=1)).isoformat())
        db.end_session(s1, 100, 60)
        db.create_session(device_id, "timed", (datetime.now() + timedelta(hours=2)).isoformat())
        report = ReportService.generate_report("custom",
            status_filter="completed",
            start_date=(datetime.now() - timedelta(days=1)).isoformat(),
            end_date=(datetime.now() + timedelta(days=1)).isoformat(),
        )
        assert report["summary"]["total_sessions"] == 1


class TestFormatReportForDisplay:
    def test_contains_summary_lines(self, test_db):
        report = ReportService.generate_report("today")
        output = ReportService.format_report_for_display(report)
        assert "Report: TODAY" in output
        assert "Total Sessions: 0" in output
        assert "Total Revenue: 0 MKD" in output


class TestGetDeviceReport:
    def test_delegates_with_device_filter(self, test_db):
        device_id = db.create_device("PS1", 100)
        report = ReportService.get_device_report(device_id, "today")
        assert report["filters"]["device_id"] == device_id


class TestGetPeriodOptions:
    def test_returns_four_options(self):
        options = ReportService.get_period_options()
        assert len(options) == 4
        values = [o["value"] for o in options]
        assert "today" in values
        assert "week" in values
        assert "month" in values
        assert "custom" in values
