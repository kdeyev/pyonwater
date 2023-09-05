import json
from typing import Any

from aiohttp import web

from pyonwater import Account, Client
from pyonwater.models import EOWUnits


def is_unit(string: str) -> bool:
    """Verify is the string is pyonwater supported measurement unit."""
    try:
        EOWUnits(string)
        return True
    except ValueError:
        return False


def replace_units(data: Any, new_unit: str) -> Any:
    """Replace EOW units in JSON recursively."""
    if isinstance(data, dict):
        for k in data:
            data[k] = replace_units(data[k], new_unit)
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = replace_units(data[i], new_unit)
        return data
    elif is_unit(data):
        return new_unit
    else:
        return data


async def mock_signin_endpoint(request):
    """Sign in HTTP endpoint mock."""
    return web.Response(text="Hello, world", headers={"cookies": "key=val"})


def mock_get_meters_endpoint(request):
    """Fetch meters endpoit mock."""
    data = """  AQ.Views.MeterPicker.meters = [{"display_address": "", "": "", "meter_uuid": "123", "meter_id": "456", "city": "", "location_name": "", "has_leak": false, "state": "", "serial_number": "789", "utility_uuid": "123", "page": 1, "zip_code": ""}];
            junk"""

    return web.Response(text=data)


def build_data_endpoint(filename: str):
    """ "Build an endpoint with data coming from mock data file."""

    def read_data(request):
        with open(f"tests//mock_data/{filename}.json") as f:
            return web.Response(text=f.read())

    return read_data


def build_data_with_units_endpoint(filename: str, units: str):
    """ "Build an endpoint with data coming from mock data file and specific unit."""

    def read_data(request):
        with open(f"tests//mock_data/{filename}.json") as f:
            data = json.load(f)
            data = replace_units(data, units)
            return web.Response(text=json.dumps(data))

    return read_data


def change_units_decorator(endpoint, new_unit):
    """Decorator for replacing EOW units in another endpoint response."""

    def change_units_endpoint(request):
        resp = endpoint(request)
        data = json.loads(resp.text)
        data = replace_units(data, new_unit)
        resp.text = json.dumps(data)
        return resp

    return change_units_endpoint


def add_error_decorator(endpoint, code: int):
    """Decorator for adding one error to another endpoint. The second call will be successful."""
    counter = 0

    def mock(request):
        nonlocal counter
        if counter == 0:
            counter += 1
            return web.Response(status=code)
        else:
            return endpoint(request)

    return mock


"""Mock for read meter request"""
mock_read_meter_endpoint = build_data_endpoint("read_meter_mock_anonymized")

"""Mock for historical data request"""
mock_historical_data_endpoint = build_data_endpoint("historical_data_mock_anonymized")


async def build_client(websession) -> tuple[Account, Client]:
    """Build authenticated client."""
    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()
    return account, client
