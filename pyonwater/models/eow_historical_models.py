# ruff: noqa

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .units import EOWUnits


class Register0EncoderItem(BaseModel):
    dials: Optional[int] = None


class Hit(BaseModel):
    # Mandatory fields
    meter_timezone: list[str] = Field(..., alias="meter.timezone")

    # Optional fields
    meter_communication_seconds: Optional[list[int]] = Field(
        None, alias="meter.communication_seconds"
    )
    register_0_encoder: Optional[list[Register0EncoderItem]] = Field(
        None, alias="register_0.encoder"
    )
    location_location_uuid: Optional[list[str]] = Field(
        None, alias="location.location_uuid"
    )
    meter_fluid_type: Optional[list[str]] = Field(None, alias="meter.fluid_type")
    meter_meter_id: Optional[list[str]] = Field(None, alias="meter.meter_id")
    account_full_name: Optional[list[str]] = Field(None, alias="account.full_name")
    meter_meter_uuid: Optional[list[str]] = Field(None, alias="meter.meter_uuid")
    meter_has_endpoint: Optional[list[bool]] = Field(None, alias="meter.has_endpoint")
    meter_serial_number: Optional[list[str]] = Field(None, alias="meter.serial_number")
    account_account_id: Optional[list[str]] = Field(None, alias="account.account_id")
    location_location_name: Optional[list[str]] = Field(
        None, alias="location.location_name"
    )
    service_service_id: Optional[list[str]] = Field(None, alias="service.service_id")
    register_0_serial_number: Optional[list[str]] = Field(
        None, alias="register_0.serial_number"
    )
    utility_utility_uuid: Optional[list[str]] = Field(
        None, alias="utility.utility_uuid"
    )
    account_account_uuid: Optional[list[str]] = Field(
        None, alias="account.account_uuid"
    )


class Params(BaseModel):
    # Optional fields
    start_date_utc: Optional[float] = None
    date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    end_date_utc: Optional[float] = None
    compare: Optional[bool] = None
    read_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date_tz: Optional[str] = None
    aggregate: Optional[str] = None
    aggregate_group: Optional[str] = None
    perspective: Optional[str] = None
    units: Optional[EOWUnits] = None
    start_date_tz: Optional[str] = None
    adjust_to: Optional[bool] = None
    combine_group: Optional[bool] = None


class Series(BaseModel):
    # Mandatory fields
    date: datetime
    display_unit: Optional[EOWUnits] = None
    bill_read: Optional[float] = None

    # Optional fields
    end_date: Optional[datetime] = None
    meter_uuid: Optional[int] = None
    value: Optional[float] = None
    start_date: Optional[datetime] = None
    register_number: Optional[int] = None
    estimated: Optional[int] = None
    raw_read: Optional[int] = None
    unit: Optional[EOWUnits] = None


class Legend(BaseModel):
    # Optional fields
    supply_zone_id: Optional[str] = None
    location_name: Optional[str] = None
    account_id: Optional[str] = None
    demand_zone_id: Optional[str] = None
    meter_id: Optional[str] = None
    full_name: Optional[str] = None
    serial_number: Optional[str] = None


class TimeSerie(BaseModel):
    # Mandatory fields
    series: list[Series]

    # Optional fields
    legend: Optional[Legend] = None


class HistoricalData(BaseModel):
    # Mandatory fields
    hit: Hit
    timeseries: dict[str, TimeSerie]

    # Optional fields
    min_chart_aggregation: Optional[str] = None
    params: Optional[Params] = None
    timezone: Optional[str] = None
    min_aggregation_seconds: Optional[int] = None
    annotations: Optional[list[str]] = None
