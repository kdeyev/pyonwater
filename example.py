"""Example showing the EOW Client usage."""

import asyncio
import logging
from datetime import datetime, timezone

import aiohttp
from aiohttp import ClientTimeout

from pyonwater import (
    Account,
    AggregationLevel,
    Client,
    EyeOnWaterAPIError,
    EyeOnWaterAuthError,
    EyeOnWaterRateLimitError,
    RequestUnits,
    enforce_monotonic_total,
    filter_points_after,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.addHandler(logging.StreamHandler())


async def main() -> None:
    """Main example demonstrating pyonwater features."""
    _LOGGER.info("Starting pyonwater example")
    
    # Configure account
    account = Account(
        eow_hostname="eyeonwater.com",
        username="your EOW login",
        password="your EOW password",
    )
    
    # Configure custom timeout (optional)
    timeout = ClientTimeout(total=30, connect=10, sock_read=20)
    
    # Use async context manager for proper resource cleanup
    async with aiohttp.ClientSession() as websession:
        client = Client(websession=websession, account=account, timeout=timeout)
        
        try:
            # Authenticate
            await client.authenticate()
            _LOGGER.info("Authentication successful")
            
            # Fetch all meters
            meters = await account.fetch_meters(client=client)
            _LOGGER.info("Meters found: %i", len(meters))
            
            for meter in meters:
                # Read current meter info
                await meter.read_meter_info(client=client)
                _LOGGER.info("Meter UUID: %s", meter.meter_uuid)
                _LOGGER.info("Current reading: %s", meter.reading)
                _LOGGER.info("Meter info: %s", meter.meter_info)
                
                # Read historical data with custom aggregation and units
                await meter.read_historical_data(
                    client=client,
                    days_to_load=7,
                    aggregation=AggregationLevel.DAILY,
                    units=RequestUnits.GALLONS,
                )
                
                # Process historical data
                if meter.last_historical_data:
                    # Filter to only recent data (example: last 3 days)
                    cutoff = datetime.now(tz=timezone.utc)
                    recent = filter_points_after(
                        meter.last_historical_data,
                        since=cutoff.replace(day=cutoff.day - 3),
                    )
                    
                    # Ensure monotonically increasing totals
                    normalized = enforce_monotonic_total(recent, clamp_min=0.0)
                    
                    _LOGGER.info(
                        "Historical data points (normalized): %i",
                        len(normalized),
                    )
                    for point in normalized[:5]:  # Show first 5
                        _LOGGER.info(
                            "  %s: %s %s",
                            point.dt,
                            point.reading,
                            point.unit,
                        )
                
        except EyeOnWaterAuthError:
            _LOGGER.error("Authentication failed - check credentials")
        except EyeOnWaterRateLimitError:
            _LOGGER.error("Rate limit exceeded - please retry later")
        except EyeOnWaterAPIError as e:
            _LOGGER.error("API error: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
