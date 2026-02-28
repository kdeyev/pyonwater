"""Tests for Series flexible date parsing (pydantic v2 field_validator)."""  # nosec: B101, B106

from datetime import datetime

import pytest

from pyonwater.models.eow_historical_models import Series


def test_series_date_parsing_full_datetime() -> None:
    """Test Series accepts a datetime object directly."""
    series = Series(
        date=datetime(2026, 2, 10, 0, 0, 0),
        meter_uuid=521577795832501,
        value=166.10,
    )
    assert series.date == datetime(2026, 2, 10, 0, 0, 0)  # nosec: B101


def test_series_date_parsing_space_separated() -> None:
    """Test Series parses space-separated datetime from actual API format."""
    series = Series.model_validate(
        {"date": "2026-02-10 00:00:00", "meter_uuid": 521577795832501, "value": 166.10}
    )
    assert series.date == datetime(2026, 2, 10, 0, 0, 0)  # nosec: B101


def test_series_date_parsing_iso_datetime() -> None:
    """Test Series parses ISO T-separated datetime."""
    series = Series.model_validate(
        {"date": "2026-02-10T00:00:00", "meter_uuid": 521577795832501, "value": 166.10}
    )
    assert series.date == datetime(2026, 2, 10, 0, 0, 0)  # nosec: B101


def test_series_date_parsing_date_only() -> None:
    """Test Series parses date-only format (YYYY-MM-DD)."""
    series = Series.model_validate(
        {"date": "2026-02-10", "meter_uuid": 521577795832501, "value": 166.10}
    )
    assert series.date == datetime(2026, 2, 10, 0, 0, 0)  # nosec: B101


def test_series_date_parsing_month_only() -> None:
    """Test Series parses month-only format used by monthly aggregation.

    The API returns YYYY-MM dates for monthly aggregation levels.
    This is the critical case that was failing before the fix.
    """
    series = Series.model_validate(
        {"date": "2026-02", "meter_uuid": 521577795832501, "value": 7.73}
    )
    assert series.date == datetime(2026, 2, 1, 0, 0, 0)  # nosec: B101


def test_series_date_parsing_year_only() -> None:
    """Test Series parses year-only format used by yearly aggregation."""
    series = Series.model_validate(
        {"date": "2026", "meter_uuid": 521577795832501, "value": 1000.0}
    )
    assert series.date == datetime(2026, 1, 1, 0, 0, 0)  # nosec: B101


def test_series_date_parsing_invalid_format() -> None:
    """Test Series raises ValueError for an unrecognised date string."""
    with pytest.raises(ValueError, match="Unable to parse date"):
        Series.model_validate(
            {"date": "not-a-date", "meter_uuid": 521577795832501, "value": 166.10}
        )


def test_series_date_parsing_invalid_type() -> None:
    """Test Series raises ValueError for non-string, non-datetime input."""
    with pytest.raises(ValueError, match="Date must be a string or datetime"):
        Series.model_validate(
            {"date": 12345, "meter_uuid": 521577795832501, "value": 166.10}
        )
