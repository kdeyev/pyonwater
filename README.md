# pyonwater
[EyeOnWater](eyeonwater.com) client library

[![Coverage Status](https://coveralls.io/repos/github/kdeyev/pyonwater/badge.svg?branch=main)](https://coveralls.io/github/kdeyev/pyonwater?branch=main)

The usage example:

```
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

        # Read historical data
        await meter.read_historical_data(client=client, days_to_load=3)
        for d in meter.last_historical_data:
            print(d)

    await websession.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

```

## Historical interval timestamps

Hourly and quarter-hour historical data use canonical interval boundaries:

- `DataPoint.dt` is the inclusive bucket start.
- `DataPoint.end_dt` is the exclusive bucket end when the boundary is known.
- `DataPoint.reading` is the cumulative register value at the end of the interval.
- `DataPoint.flow_value` is the usage during `[dt, end_dt)` when supplied by EyeOnWater.

EyeOnWater labels some intervals by their final minute (`:14`, `:29`, `:44`,
or `:59`). The client normalizes those labels rather than exposing them as
bucket starts. For resolutions without verified boundary semantics, `end_dt`
remains `None`.
