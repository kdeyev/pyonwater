import json
from typing import Any

from aiohttp import web

from pyonwater.models import EOWUnits


def is_unit(string: str) -> bool:
    """Verify is the string is pyonwater supported measurement unit"""
    try:
        EOWUnits(string)
        return True
    except ValueError:
        return False


def replace_units(data: Any, new_unit: str) -> Any:
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


async def mock_signin_enpoint(request):
    """Mock for sign in HTTP call"""
    resp = web.Response(text="Hello, world", headers={"cookies": "key=val"})
    return resp


def mock_get_meters_endpoint(request):
    data = """  AQ.Views.MeterPicker.meters = [{"display_address": "", "": "", "meter_uuid": "123", "meter_id": "456", "city": "", "location_name": "", "has_leak": false, "state": "", "serial_number": "789", "utility_uuid": "123", "page": 1, "zip_code": ""}];
            junk"""

    return web.Response(text=data)


def build_data_endpoint(filename: str):
    def read_data(request):
        with open(f"tests//mock_data/{filename}.json") as f:
            return web.Response(text=f.read())

    return read_data


def build_data_with_units_endpoint(filename: str, units: str):
    def read_data(request):
        with open(f"tests//mock_data/{filename}.json") as f:
            data = json.load(f)
            data = replace_units(data, units)
            return web.Response(text=json.dumps(data))

    return read_data


# def mock_historical_data_endpoint(request):
#     """Mock for historical datas request"""
#     with open("tests//mock_data/historical_data_mock_anonymized.json") as f:
#         return web.Response(text=f.read())


# def mock_read_meter_custom_units(new_unit):
#     def mock_read_meter(request):
#         with open("tests//mock_data/read_meter_mock_anonymized.json") as f:
#             data = json.load(f)
#             data = replace_units(data, new_unit)
#             return web.Response(text=json.dumps(data))

#     return mock_read_meter


def change_units_decorator(endpoint, new_unit):
    def change_units_endpoint(request):
        resp = endpoint(request)
        data = json.loads(resp.text)
        data = replace_units(data, new_unit)
        resp.text = json.dumps(data)
        return resp

    return change_units_endpoint


def add_error_decorator(endpoint, code: int):
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
mock_read_meter_endpont = build_data_endpoint("read_meter_mock_anonymized")

"""Mock for historical data request"""
mock_historical_data_endpoint = build_data_endpoint("historical_data_mock_anonymized")

"""Mock for historical data request, but no actual data"""
mock_historical_data_nodata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_nodata"
)

"""Mock for historical data request, but newer data"""
mock_historical_data_newer_data_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data"
)

"""Mock for historical data request, but newer and more data"""
mock_historical_data_newerdata_moredata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data_moredata"
)

# def mock_historical_nodata(request):
#     with open("tests//mock_data/historical_data_mock_anonymized_nodata.json") as f:
#         return web.Response(text=f.read())


# def mock_historical_newerdata(request):
#     with open("tests//mock_data/historical_data_mock_anonymized_newer_data.json") as f:
#         return web.Response(text=f.read())


# def mock_historical_newerdata_moredata(request):
#     with open(
#         "tests//mock_data/historical_data_mock_anonymized_newer_data_moredata.json"
#     ) as f:
#         return web.Response(text=f.read())


# def mock_read_meter_custom_units(new_unit):
#     def mock_read_meter(request):
#         with open("tests//mock_data/read_meter_mock_anonymized.json") as f:
#             data = json.load(f)
#             data = replace_units(data, new_unit)
#             return web.Response(text=json.dumps(data))

#     return mock_read_meter


# def mock_historical_data_custom_units(new_unit):
#     def mock_read_meter(request):
#         with open("tests//mock_data/historical_data_mock_anonymized.json") as f:
#             data = json.load(f)
#             data = replace_units(data, new_unit)
#             return web.Response(text=json.dumps(data))

#     return mock_read_meter
