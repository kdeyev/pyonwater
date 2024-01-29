"""Example showing the EOW Client usage."""

import asyncio
import logging

import aiohttp

from pyonwater import Account, Client

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.addHandler(logging.StreamHandler())


async def main() -> None:
    """Main."""

    _LOGGER.info("Starting example")
    account = Account(
        eow_hostname="eyeonwater.com",
        username="your EOW login",
        password="your EOW password",
    )
    websession = aiohttp.ClientSession()
    client = Client(websession=websession, account=account)

    await client.authenticate()

    meters = await account.fetch_meters(client=client)
    _LOGGER.info("Meters found: %i", len(meters))
    for meter in meters:
        # Read meter info
        await meter.read_meter_info(client=client)
        _LOGGER.info("Meter info: %s", meter.meter_info)
        _LOGGER.info("Meter reading: %s", meter.reading)

        # Read historical data
        await meter.read_historical_data(client=client, days_to_load=3)
        for d in meter.last_historical_data:
            _LOGGER.info("Historical data: %s %s %s", d.dt, d.reading, d.unit)

    await websession.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
