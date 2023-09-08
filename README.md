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
