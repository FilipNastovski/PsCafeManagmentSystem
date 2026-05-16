"""Unit tests for PricingService — pure functions, no DB dependency."""
import pytest
from datetime import datetime, timedelta

from services.pricing_service import PricingService


class TestCalculatePrice:
    def test_exact_hour(self):
        assert PricingService.calculate_price(100, 60) == 100

    def test_half_hour(self):
        assert PricingService.calculate_price(100, 30) == 50

    def test_one_minute(self):
        assert PricingService.calculate_price(60, 1) == 1

    def test_fractional_rounds_up(self):
        # 60.5 minutes should round up to 61
        assert PricingService.calculate_price(60, 60.5) == 61

    def test_zero_minutes(self):
        assert PricingService.calculate_price(100, 0) == 0

    def test_negative_minutes(self):
        assert PricingService.calculate_price(100, -5) == 0

    def test_high_rate(self):
        assert PricingService.calculate_price(200, 30) == 100


class TestCalculateEstimatedPrice:
    def test_exact(self):
        assert PricingService.calculate_estimated_price(100, 60) == 100

    def test_partial(self):
        assert PricingService.calculate_estimated_price(100, 15) == 25

    def test_zero(self):
        assert PricingService.calculate_estimated_price(100, 0) == 0


class TestCalculateBilledMinutes:
    def test_exact_minute(self):
        start = datetime.now()
        end = start + timedelta(minutes=30)
        assert PricingService.calculate_billed_minutes(
            start.isoformat(), end.isoformat()
        ) == 30

    def test_fractional_seconds_round_up(self):
        start = datetime.now()
        end = start + timedelta(minutes=1, seconds=30)
        assert PricingService.calculate_billed_minutes(
            start.isoformat(), end.isoformat()
        ) == 2

    def test_minimum_one(self):
        start = datetime.now()
        end = start + timedelta(seconds=10)
        assert PricingService.calculate_billed_minutes(
            start.isoformat(), end.isoformat()
        ) >= 1

    def test_defaults_to_now(self):
        start = (datetime.now() - timedelta(minutes=10)).isoformat()
        result = PricingService.calculate_billed_minutes(start)
        assert result >= 10


class TestCalculateRemainingTime:
    def test_positive_remaining(self):
        future = (datetime.now() + timedelta(minutes=30)).isoformat()
        remaining = PricingService.calculate_remaining_time(future)
        assert remaining > 0

    def test_negative_overdue(self):
        past = (datetime.now() - timedelta(minutes=10)).isoformat()
        remaining = PricingService.calculate_remaining_time(past)
        assert remaining < 0


class TestCalculateElapsedMinutes:
    def test_with_end_time(self):
        start = (datetime.now() - timedelta(minutes=45)).isoformat()
        end = datetime.now().isoformat()
        assert PricingService.calculate_elapsed_minutes(start, end) >= 44

    def test_defaults_to_now(self):
        start = (datetime.now() - timedelta(minutes=20)).isoformat()
        assert PricingService.calculate_elapsed_minutes(start) >= 19

    def test_minimum_one(self):
        now = datetime.now().isoformat()
        assert PricingService.calculate_elapsed_minutes(now, now) == 1


class TestFormatPrice:
    def test_basic(self):
        assert PricingService.format_price(500) == "500 MKD"

    def test_zero(self):
        assert PricingService.format_price(0) == "0 MKD"


class TestFormatDuration:
    def test_minutes_only(self):
        assert PricingService.format_duration(30) == "30m"

    def test_exact_hour(self):
        assert PricingService.format_duration(60) == "1h"

    def test_hours_and_minutes(self):
        assert PricingService.format_duration(90) == "1h 30m"

    def test_multiple_hours(self):
        assert PricingService.format_duration(180) == "3h"


class TestFormatTimeRemaining:
    def test_positive(self):
        assert PricingService.format_time_remaining(30) == "30m"

    def test_negative(self):
        assert PricingService.format_time_remaining(-5) == "-5m"

    def test_hours(self):
        assert PricingService.format_time_remaining(90) == "1h 30m"


class TestFormatExpectedEnd:
    def test_format(self):
        dt = datetime(2026, 5, 16, 14, 30, 0)
        assert PricingService.format_expected_end(dt.isoformat()) == "14:30"


class TestCalculateNewExpectedEnd:
    def test_add_minutes(self):
        current = datetime(2026, 5, 16, 14, 0, 0).isoformat()
        new_end = PricingService.calculate_new_expected_end(current, 30)
        assert "14:30" in new_end

    def test_add_hours(self):
        current = datetime(2026, 5, 16, 10, 0, 0).isoformat()
        new_end = PricingService.calculate_new_expected_end(current, 120)
        assert "12:00" in new_end
