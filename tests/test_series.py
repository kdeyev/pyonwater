"""Tests for series helpers."""  # nosec: B101, B106

from datetime import datetime

from pyonwater import DataPoint, enforce_monotonic_total, filter_points_after


def test_enforce_monotonic_total_clamps_decreases() -> None:
    """Ensure decreasing readings are clamped to the previous max."""
    points = [
        DataPoint(dt=datetime(2024, 1, 1, 0, 0), reading=5.0, unit="gal"),
        DataPoint(dt=datetime(2024, 1, 1, 1, 0), reading=3.0, unit="gal"),
        DataPoint(dt=datetime(2024, 1, 1, 2, 0), reading=7.0, unit="gal"),
    ]

    normalized = enforce_monotonic_total(points)

    assert [p.reading for p in normalized] == [5.0, 5.0, 7.0]  # nosec: B101


def test_enforce_monotonic_total_empty() -> None:
    """Ensure empty input returns empty output."""
    assert not enforce_monotonic_total([])  # nosec: B101


def test_filter_points_after_cutoff() -> None:
    """Ensure only points after cutoff are returned."""
    points = [
        DataPoint(dt=datetime(2024, 1, 1, 0, 0), reading=1.0, unit="gal"),
        DataPoint(dt=datetime(2024, 1, 1, 1, 0), reading=2.0, unit="gal"),
        DataPoint(dt=datetime(2024, 1, 1, 2, 0), reading=3.0, unit="gal"),
        DataPoint(dt=datetime(2024, 1, 1, 3, 0), reading=4.0, unit="gal"),
    ]

    cutoff = datetime(2024, 1, 1, 1, 30)  # Between first and second points
    filtered = filter_points_after(points, since=cutoff)

    assert len(filtered) == 2  # nosec: B101
    assert [p.reading for p in filtered] == [3.0, 4.0]  # nosec: B101


def test_filter_points_after_none_since() -> None:
    """Ensure None since returns all points."""
    points = [
        DataPoint(dt=datetime(2024, 1, 1, 0, 0), reading=1.0, unit="gal"),
        DataPoint(dt=datetime(2024, 1, 1, 1, 0), reading=2.0, unit="gal"),
    ]

    filtered = filter_points_after(points, since=None)

    assert len(filtered) == 2  # nosec: B101
    assert filtered == points  # nosec: B101


def test_filter_points_after_all_filtered() -> None:
    """Ensure all points can be filtered if cutoff is after all points."""
    points = [
        DataPoint(dt=datetime(2024, 1, 1, 0, 0), reading=1.0, unit="gal"),
        DataPoint(dt=datetime(2024, 1, 1, 1, 0), reading=2.0, unit="gal"),
    ]

    cutoff = datetime(2024, 1, 2, 0, 0)  # After all points
    filtered = filter_points_after(points, since=cutoff)

    assert len(filtered) == 0  # nosec: B101


def test_enforce_monotonic_total_clamp_min() -> None:
    """Verify readings below clamp_min are clamped up to clamp_min."""
    points = [
        DataPoint(dt=datetime(2026, 1, 1, 0, 0), reading=-5.0, unit="gal"),
        DataPoint(dt=datetime(2026, 1, 1, 1, 0), reading=10.0, unit="gal"),
    ]

    result = enforce_monotonic_total(points, clamp_min=0.0)

    assert result[0].reading == 0.0  # nosec: B101 — clamped from -5
    assert result[1].reading == 10.0  # nosec: B101 — unchanged
