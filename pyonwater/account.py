"""EyeOnWater API integration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast
import urllib.parse

from .exceptions import EyeOnWaterAPIError
from .meter import Meter
from .meter_reader import MeterReader

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client

DASHBOARD_ENDPOINT = "/dashboard/"
NEW_SEARCH_ENDPOINT = "/api/2/residential/new_search"
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
    ) -> None:
        """Initialize the account."""
        self.eow_hostname = eow_hostname
        self.username = username
        self.password = password

    async def fetch_meter_readers(
        self,
        client: Client,
        *,
        prefer_new_search: bool = False,
    ) -> list[MeterReader]:
        """List the meter readers associated with the account.

        Args:
            client: The authenticated API client.
            prefer_new_search: When True, try the new_search API first and
                fall back to the legacy dashboard scrape.  When False
                (default), use the dashboard first and fall back to
                new_search.
        """
        if prefer_new_search:
            new_search_meters = await self.fetch_meter_readers_new_search(client)
            if new_search_meters:
                return new_search_meters
            return await self._fetch_meter_readers_dashboard(client)

        dashboard_meters = await self._fetch_meter_readers_dashboard(client)
        if dashboard_meters:
            return dashboard_meters
        return await self.fetch_meter_readers_new_search(client)

    async def _fetch_meter_readers_dashboard(self, client: Client) -> list[MeterReader]:
        """Fetch meters by scraping the legacy dashboard page."""
        try:
            path = DASHBOARD_ENDPOINT + urllib.parse.quote(self.username)
            data = await client.request(path=path, method="get")
        except EyeOnWaterAPIError:
            return []

        meters: list[MeterReader] = []
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

                    meter_uuid: str = meter_info[METER_UUID_FIELD]
                    meter_id: str = meter_info[METER_ID_FIELD]

                    meter = MeterReader(
                        meter_uuid=meter_uuid,
                        meter_id=meter_id,
                    )
                    meters.append(meter)

        return meters

    async def fetch_meter_readers_new_search(self, client: Client) -> list[MeterReader]:
        """Fetch meters using the API endpoint used by modern EyeOnWater flows."""
        try:
            raw = await client.request(
                path=NEW_SEARCH_ENDPOINT,
                method="post",
                json={"query": {"match_all": {}}},
            )
            payload: dict[str, Any] = json.loads(raw)
        except (EyeOnWaterAPIError, json.JSONDecodeError, TypeError, ValueError):
            return []

        elastic: dict[str, Any] = payload.get("elastic_results") or {}
        hits_wrapper: dict[str, Any] = elastic.get("hits") or {}
        hits: list[Any] = hits_wrapper.get("hits") or []
        meters: list[MeterReader] = []
        for hit in hits:
            source: dict[str, Any] = hit.get("_source") or {}
            meter_obj_raw: Any = source.get("meter")
            meter_obj: dict[str, Any] = (
                cast(dict[str, Any], meter_obj_raw)
                if isinstance(meter_obj_raw, dict)
                else {}
            )

            meter_uuid: str | None = (
                meter_obj.get("meter_uuid")
                or source.get(METER_UUID_FIELD)
                or source.get("meter.meter_uuid")
            )
            meter_id: str | None = (
                meter_obj.get("meter_id")
                or source.get(METER_ID_FIELD)
                or source.get("meter.meter_id")
            )
            if not meter_uuid or not meter_id:
                continue

            meters.append(MeterReader(meter_uuid=meter_uuid, meter_id=str(meter_id)))

        return meters

    async def fetch_meters(
        self,
        client: Client,
        *,
        prefer_new_search: bool = False,
    ) -> list[Meter]:
        """List the meter states associated with the account."""
        meter_readers = await self.fetch_meter_readers(
            client, prefer_new_search=prefer_new_search
        )
        meters: list[Meter] = []
        for reader in meter_readers:
            meter_info = await reader.read_meter_info(client)
            meters.append(Meter(reader, meter_info))

        return meters
