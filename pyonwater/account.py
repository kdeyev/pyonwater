"""EyeOnWater API integration."""
from __future__ import annotations

from typing import TYPE_CHECKING
import urllib.parse

from .exceptions import EyeOnWaterAPIError
from .meter import Meter
from .meter_reader import MeterReader

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client

DASHBOARD_ENDPOINT = "/dashboard/"
METER_UUID_FIELD = "meter_uuid"
METER_ID_FIELD = "meter_id"
INFO_PREFIX = "AQ.Views.MeterPicker.meters = "


class Account:
    """Class represents account object."""

    def __init__(
        self,
        eow_hostname: str,
        username: str,
        password: str,
        metric_measurement_system: bool,
    ) -> None:
        """Initialize the account."""
        self.eow_hostname = eow_hostname
        self.username = username
        self.password = password
        self.metric_measurement_system = metric_measurement_system

    async def fetch_meter_readers(self, client: Client) -> list[MeterReader]:
        """List the meter readers associated with the account."""
        path = DASHBOARD_ENDPOINT + urllib.parse.quote(self.username)
        data = await client.request(path=path, method="get")

        meters = []
        lines = data.split("\n")
        for line in lines:
            if INFO_PREFIX in line:
                meter_infos = client.extract_json(line, INFO_PREFIX)
                for meter_info in meter_infos:
                    if METER_UUID_FIELD not in meter_info:
                        msg = f"Cannot find {METER_UUID_FIELD} field"
                        raise EyeOnWaterAPIError(
                            msg,
                        )

                    meter_uuid = meter_info[METER_UUID_FIELD]
                    meter_id = meter_info[METER_ID_FIELD]

                    meter = MeterReader(
                        meter_uuid=meter_uuid,
                        meter_id=meter_id,
                        metric_measurement_system=self.metric_measurement_system,
                    )
                    meters.append(meter)

        return meters

    async def fetch_meters(self, client: Client) -> list[Meter]:
        """List the meter states associated with the account."""
        meter_readers = await self.fetch_meter_readers(client)
        return [Meter(reader) for reader in meter_readers]
