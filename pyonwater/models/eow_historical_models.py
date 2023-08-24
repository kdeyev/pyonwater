# ruff: noqa

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .units import EOWUnits


class Register0EncoderItem(BaseModel):
    dials: int


class Hit(BaseModel):
    meter_communication_seconds: list[int] = Field(
        ..., alias="meter.communication_seconds"
    )
    meter_timezone: list[str] = Field(..., alias="meter.timezone")
    register_0_encoder: list[Register0EncoderItem] = Field(
        ..., alias="register_0.encoder"
    )
    location_location_uuid: list[str] = Field(..., alias="location.location_uuid")
    meter_fluid_type: list[str] = Field(..., alias="meter.fluid_type")
    meter_meter_id: list[str] = Field(..., alias="meter.meter_id")
    account_full_name: list[str] = Field(..., alias="account.full_name")
    meter_meter_uuid: list[str] = Field(..., alias="meter.meter_uuid")
    meter_has_endpoint: list[bool] = Field(..., alias="meter.has_endpoint")
    meter_serial_number: list[str] = Field(..., alias="meter.serial_number")
    account_account_id: list[str] = Field(..., alias="account.account_id")
    location_location_name: list[str] = Field(..., alias="location.location_name")
    service_service_id: list[str] = Field(..., alias="service.service_id")
    register_0_serial_number: list[str] = Field(..., alias="register_0.serial_number")
    utility_utility_uuid: list[str] = Field(..., alias="utility.utility_uuid")
    account_account_uuid: list[str] = Field(..., alias="account.account_uuid")


class Params(BaseModel):
    start_date_utc: float
    date: datetime
    end_date: datetime
    end_date_utc: float
    compare: bool
    read_type: str
    start_date: datetime
    end_date_tz: str
    aggregate: str
    aggregate_group: str
    perspective: str
    units: EOWUnits
    start_date_tz: str
    adjust_to: bool
    combine_group: bool


class Series(BaseModel):
    bill_read: float
    end_date: datetime
    display_unit: EOWUnits
    meter_uuid: int
    value: float
    start_date: datetime
    date: datetime
    register_number: int
    estimated: int
    raw_read: int
    unit: EOWUnits


class Legend(BaseModel):
    supply_zone_id: str
    location_name: str
    account_id: str
    demand_zone_id: str
    meter_id: str
    full_name: str
    serial_number: str


class TimeSerie(BaseModel):
    series: list[Series]
    legend: Legend


class HistoricalData(BaseModel):
    hit: Hit
    min_chart_aggregation: str
    params: Params
    timeseries: dict[str, TimeSerie]
    timezone: str
    min_aggregation_seconds: int
    annotations: list[str]
