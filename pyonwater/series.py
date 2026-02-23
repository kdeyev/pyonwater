"""Helpers for data series normalization."""

from __future__ import annotations

from datetime import datetime

from .models import DataPoint


def enforce_monotonic_total(
    points: list[DataPoint], *, clamp_min: float | None = None
) -> list[DataPoint]:
    """Return a non-decreasing series by clamping downward steps.

    This is useful for total-reading series where resets or rounding can
    produce decreases that would otherwise break statistic calculations.
    """
    if not points:
        return []

    normalized: list[DataPoint] = []
    last_value: float | None = None

    for point in points:
        reading = point.reading
        if clamp_min is not None and reading < clamp_min:
            reading = clamp_min

        if last_value is None:
            last_value = reading
        elif reading < last_value:
            reading = last_value
        else:
            last_value = reading

        normalized.append(DataPoint(dt=point.dt, reading=reading, unit=point.unit))

    return normalized


def filter_points_after(
    points: list[DataPoint], since: datetime | None = None
) -> list[DataPoint]:
    """Return only points after a given timestamp.

    Useful for avoiding duplicate/overlapping data when importing historical
    series into statistics engines.

    Args:
        points: List of data points to filter.
        since: Cutoff timestamp. Only points with dt > since are returned.
               If None, returns all points.

    Returns:
        Filtered list of data points.
    """
    if since is None:
        return points
    return [p for p in points if p.dt > since]
