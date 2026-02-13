# pyonwater

[EyeOnWater](eyeonwater.com) client library

[![Coverage Status](https://coveralls.io/repos/github/kdeyev/pyonwater/badge.svg?branch=main)](https://coveralls.io/github/kdeyev/pyonwater?branch=main)

## Features

- **Async/await** - Built on aiohttp for efficient async operations
- **Type-safe** - Full type hints and Pydantic v2 validation
- **Production-ready** - Configurable timeouts, automatic retries with exponential backoff
- **Comprehensive** - Access meter readings, historical data, and account information
- **Flexible units** - Support for gallons, cubic feet, liters, cubic meters, and more
- **Data processing** - Utilities for monotonic enforcement, filtering, and unit conversion
- **Well-tested** - 97% test coverage with extensive validation

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
    
    async with aiohttp.ClientSession() as websession:
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


asyncio.run(main())
```

## Advanced Usage

### Configuring Request Timeouts

The client includes robust timeout configuration to prevent hung requests:

```python
from aiohttp import ClientTimeout

# Custom timeout configuration
timeout = ClientTimeout(
    total=30,      # Maximum time for entire request (seconds)
    connect=10,    # Maximum time to establish connection
    sock_read=20   # Maximum time to read data from socket
)

client = Client(websession=websession, account=account, timeout=timeout)
```

Default timeout values are: `total=30s`, `connect=10s`, `sock_read=20s`.

The client automatically retries on authentication expiration and rate limiting with exponential backoff (max 3 attempts).

### Error Handling

The library provides specific exceptions for different error scenarios:

```python
from pyonwater import (
    EyeOnWaterAuthError,       # Invalid username/password
    EyeOnWaterAuthExpired,     # Token expired (auto-retried)
    EyeOnWaterRateLimitError,  # Rate limit hit (auto-retried)
    EyeOnWaterAPIError,        # Unknown API error
    EyeOnWaterResponseIsEmpty, # Valid response but no data
    EyeOnWaterUnitError,       # Unit conversion error
)

try:
    await client.authenticate()
    meters = await account.fetch_meters(client=client)
except EyeOnWaterAuthError:
    print("Invalid credentials")
except EyeOnWaterRateLimitError:
    print("Rate limit exceeded - retry with backoff")
except EyeOnWaterAPIError as e:
    print(f"API error: {e}")
```

Note: `EyeOnWaterAuthExpired` and `EyeOnWaterRateLimitError` are automatically retried with exponential backoff.

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

### Data Processing Utilities

The library includes helper functions for processing historical data:

#### Monotonic Total Enforcement

Ensures cumulative meter readings never decrease (useful for handling resets or rounding errors):

```python
from pyonwater import enforce_monotonic_total

# Normalize historical data to be monotonically increasing
normalized = enforce_monotonic_total(
    meter.last_historical_data,
    clamp_min=0.0  # Optional: enforce minimum value
)
```

#### Time-Based Filtering

Filter data points to avoid duplicates when importing to statistics engines:

```python
from datetime import datetime
from pyonwater import filter_points_after

# Only get data after a specific time
since = datetime(2026, 1, 1, tzinfo=timezone.utc)
recent_data = filter_points_after(meter.last_historical_data, since=since)
```

#### Unit Conversion

Convert between meter native units and display units:

```python
from pyonwater import convert_to_native, deduce_native_units, EOWUnits, NativeUnits

# Deduce native units from reading unit
native = deduce_native_units(EOWUnits.UNIT_KGAL)  # Returns NativeUnits.GAL

# Convert reading to native units
gallons = convert_to_native(
    NativeUnits.GAL,
    EOWUnits.UNIT_KGAL,
    value=5.0  # 5 kGal = 5000 gallons
)
```

## Quick Reference

Common patterns for everyday use:

```python
from pyonwater import (
    Account, Client, 
    AggregationLevel, RequestUnits,
    EyeOnWaterAuthError,
)
from aiohttp import ClientSession, ClientTimeout

# Initialize with custom timeout
async with ClientSession() as session:
    timeout = ClientTimeout(total=30, connect=10, sock_read=20)
    client = Client(session, Account(...), timeout=timeout)
    
    # Authenticate
    await client.authenticate()
    
    # Get all meters
    meters = await account.fetch_meters(client)
    
    # Get current reading
    await meters[0].read_meter_info(client)
    print(meters[0].reading)
    
    # Get 30 days of hourly data in gallons
    await meters[0].read_historical_data(
        client, 
        days_to_load=30,
        aggregation=AggregationLevel.HOURLY,
        units=RequestUnits.GALLONS
    )
```

## API Documentation

For complete API parameter requirements, validation details, and endpoint documentation, see [docs/API_VALIDATION.md](docs/API_VALIDATION.md).

## Development

This library uses comprehensive input validation and type-safe enums to ensure API requests are always valid. All API parameters are validated before making requests to prevent silent failures.

See the test suite for examples of proper usage and parameter validation.
