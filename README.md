# pyonwater

[EyeOnWater](eyeonwater.com) client library

[![Coverage Status](https://coveralls.io/repos/github/kdeyev/pyonwater/badge.svg?branch=main)](https://coveralls.io/github/kdeyev/pyonwater?branch=main)

## Installation

```bash
pip install pyonwater
```

## Basic Usage

```python
"""Example showing the EOW Client usage."""

import asyncio

import aiohttp

from pyonwater import Account, Client


async def main() -> None:
    """Main."""
    account = Account(
        eow_hostname="eyeonwater.com",
        username="your EOW login",
        password="your EOW password",
    )
    websession = aiohttp.ClientSession()
    client = Client(websession=websession, account=account)

    await client.authenticate()

    meters = await account.fetch_meters(client=client)
    print(f"{len(meters)} meters found")
    for meter in meters:
        # Read meter info
        await meter.read_meter_info(client=client)
        print(f"meter {meter.meter_uuid} shows {meter.reading}")
        print(f"meter {meter.meter_uuid} info {meter.meter_info}")

        # Read historical data (default: 3 days, hourly aggregation)
        await meter.read_historical_data(client=client, days_to_load=3)
        for d in meter.last_historical_data:
            print(d)

    await websession.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

## Advanced Usage

### Specifying Units and Aggregation

You can customize the units and time granularity when reading historical data:

```python
from pyonwater.models.units import AggregationLevel, RequestUnits

# Read 7 days of data with daily aggregation in gallons
await meter.read_historical_data(
    client=client,
    days_to_load=7,
    aggregation=AggregationLevel.DAILY,
    units=RequestUnits.GALLONS
)

# Read 1 day with 15-minute intervals in cubic meters
await meter.read_historical_data(
    client=client,
    days_to_load=1,
    aggregation=AggregationLevel.QUARTER_HOURLY,
    units=RequestUnits.CUBIC_METERS
)
```

### Available Options

**Aggregation Levels:**
- `AggregationLevel.QUARTER_HOURLY` - 15-minute intervals
- `AggregationLevel.HOURLY` - 1-hour intervals (default)
- `AggregationLevel.DAILY` - 1-day intervals
- `AggregationLevel.WEEKLY` - 7-day intervals
- `AggregationLevel.MONTHLY` - 1-month intervals
- `AggregationLevel.YEARLY` - 1-year intervals

**Units:**
- `RequestUnits.GALLONS` - US gallons
- `RequestUnits.CUBIC_FEET` - Cubic feet
- `RequestUnits.CCF` - Centum cubic feet (100 ft³)
- `RequestUnits.LITERS` - Liters
- `RequestUnits.CUBIC_METERS` - Cubic meters (default)
- `RequestUnits.IMPERIAL_GALLONS` - Imperial gallons
- `RequestUnits.OIL_BARRELS` - Oil barrels
- `RequestUnits.FLUID_BARRELS` - Fluid barrels

## API Documentation

For complete API parameter requirements, validation details, and endpoint documentation, see [docs/API_VALIDATION.md](docs/API_VALIDATION.md).

## Development

This library uses comprehensive input validation and type-safe enums to ensure API requests are always valid. All API parameters are validated before making requests to prevent silent failures.

See the test suite for examples of proper usage and parameter validation.
