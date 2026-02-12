"""Test configuration and mock fixtures.

This module provides pytest fixtures and mock HTTP endpoints for testing
the pyonwater library against EyeOnWater API responses. It includes utilities
for building mock responses with various aggregation levels and units.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Any, cast

from aiohttp import web

from pyonwater import Account, Client, Meter, MeterReader
from pyonwater.models import EOWUnits


def is_unit(string: str) -> bool:
    """Verify is the string is pyonwater supported measurement unit."""
    try:
        EOWUnits(string)
        return True
    except ValueError:
        return False


def replace_units(data: Any, new_unit: str) -> Any:
    """Replace EOW units in JSON recursively.

    Args:
        data: Any JSON-compatible data structure.
        new_unit: The unit string to replace with.

    Returns:
        The data structure with all unit strings replaced.
    """
    if isinstance(data, dict):
        data_dict = cast(dict[Any, Any], data)
        for key in data_dict:
            data_dict[key] = replace_units(data_dict[key], new_unit)
        return data_dict
    if isinstance(data, list):
        data_list = cast(list[Any], data)
        for i, item in enumerate(data_list):
            data_list[i] = replace_units(item, new_unit)
        return data_list
    if is_unit(data):
        return new_unit
    return data


async def mock_signin_endpoint(_request: web.Request) -> web.Response:
    """Sign in HTTP endpoint mock."""
    return web.Response(text="Hello, world", headers={"cookies": "key=val"})


async def mock_get_meters_endpoint(_request: web.Request) -> web.Response:
    """Fetch meters endpoint mock."""
    data = (
        '  AQ.Views.MeterPicker.meters = [{"display_address": "", '
        '"": "", "meter_uuid": "123", "meter_id": "456", "city": "", '
        '"location_name": "", "has_leak": false, "state": "", '
        '"serial_number": "789", "utility_uuid": "123", "page": 1, '
        '"zip_code": ""}];\n            junk'
    )
    return web.Response(text=data)


def build_data_endpoint(
    filename: str,
) -> Callable[[web.Request], Awaitable[web.Response]]:
    """Build an endpoint with data coming from mock data file."""

    async def read_data(_request: web.Request) -> web.Response:
        with open(f"tests/mock_data/{filename}.json", encoding="utf-8") as f:
            return web.Response(text=f.read())

    return read_data


def build_data_with_units_endpoint(
    filename: str, units: str
) -> Callable[[web.Request], Awaitable[web.Response]]:
    """Build an endpoint with data from mock file with specific unit."""

    async def read_data(_request: web.Request) -> web.Response:
        with open(f"tests/mock_data/{filename}.json", encoding="utf-8") as f:
            data = json.load(f)
            data = replace_units(data, units)
            return web.Response(text=json.dumps(data))

    return read_data


def change_units_decorator(
    endpoint: Callable[[web.Request], Awaitable[web.Response]], new_unit: str
) -> Callable[[web.Request], Awaitable[web.Response]]:
    """Decorator for replacing EOW units in another endpoint response."""

    async def change_units_endpoint(_request: web.Request) -> web.Response:
        resp = await endpoint(_request)
        if resp.text is not None:
            data = json.loads(resp.text)
            data = replace_units(data, new_unit)
            resp.text = json.dumps(data)
        return resp

    return change_units_endpoint


def add_error_decorator(
    endpoint: Callable[[web.Request], Awaitable[web.Response]], code: int
) -> Callable[[web.Request], Awaitable[web.Response]]:
    """Decorator for adding one error to another endpoint.

    The second call will be successful.
    """
    counter = 0

    async def mock(_request: web.Request) -> web.Response:
        nonlocal counter
        if counter == 0:
            counter += 1
            return web.Response(status=code)
        return await endpoint(_request)

    return mock


mock_read_meter_endpoint: Callable[[web.Request], Awaitable[web.Response]] = (
    build_data_endpoint("read_meter_mock_anonymized")
)


async def mock_historical_data_endpoint(request: web.Request) -> web.Response:
    """Mock consumption endpoint that validates required parameters like real API.

    The real EyeOnWater API returns empty responses when required parameters
    are missing. This mock mimics that behavior to catch contract violations.
    """
    payload = await request.json()
    params = payload.get("params", {})

    # Validate required parameters - real API returns empty response if missing
    required_params = ["source", "aggregate", "perspective", "date", "units"]
    for param in required_params:
        if param not in params:
            # Return empty string like real API does when params are invalid
            return web.Response(text="")

    # Valid request - return mock data
    with open(
        "tests/mock_data/historical_data_mock_anonymized.json", encoding="utf-8"
    ) as f:
        return web.Response(text=f.read())


mock_historical_data_no_data_endpoint: Callable[
    [web.Request], Awaitable[web.Response]
] = build_data_endpoint("historical_data_mock_anonymized_nodata")


async def build_client(websession: Any) -> tuple[Account, Client]:
    """Build authenticated client.

    Args:
        websession: The aiohttp ClientSession to use for requests.

    Returns:
        Tuple of (Account, Client) configured for testing.
    """
    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()
    return account, client


async def build_meter(client: Client) -> Meter:
    """Build meter object.

    Args:
        client: The Client to use for fetching meter info.

    Returns:
        A Meter object configured for testing.
    """
    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    meter_info = await meter_reader.read_meter_info(client)
    return Meter(meter_reader, meter_info)


def build_consumption_endpoint_with_aggregation(
    _aggregation: str,
) -> Callable[[web.Request], Awaitable[web.Response]]:
    """Build a consumption endpoint for a specific aggregation level.

    Args:
        _aggregation: The aggregation level (e.g., 'hourly', 'daily').

    Returns:
        A mock endpoint that returns historical data with the specified
        aggregation level.
    """
    return build_data_endpoint("historical_data_mock_anonymized")


def build_at_a_glance_endpoint() -> Callable[[web.Request], Awaitable[web.Response]]:
    """Build an at_a_glance endpoint mock.

    Returns:
        A mock endpoint that returns at_a_glance data.
    """
    # For now, use the historical data as the base
    # In a real scenario, this would have specific at_a_glance mock data
    return build_data_endpoint("historical_data_mock_anonymized")
