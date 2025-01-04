# ruff: noqa

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from .units import EOWUnits


class Service(BaseModel):
    # Optional fields
    class_code_normalized: Optional[str] = None
    route: Optional[str] = None
    active: Optional[bool] = None
    class_code: Optional[str] = None
    service_type: Optional[str] = None
    service_id: Optional[str] = None
    start_date: Optional[datetime] = None
    service_point_uuid: Optional[str] = None
    cycle: Optional[str] = None


class Location(BaseModel):
    # Optional fields
    city: Optional[str] = None
    parcel_number: Optional[str] = None
    location_name: Optional[str] = None
    parity: Optional[str] = None
    country: Optional[str] = None
    route: Optional[str] = None
    geocode_status: Optional[int] = None
    zip_code: Optional[str] = None
    longitude: Optional[str] = None
    display_address_3: Optional[str] = None
    state: Optional[str] = None
    location_uuid: Optional[str] = None
    county_name: Optional[str] = None
    latitude: Optional[str] = None
    display_address_2: Optional[str] = None
    location_id: Optional[str] = None
    display_address: Optional[str] = None
    display_street_name: Optional[str] = None
    cycle: Optional[str] = None


class LeakAlert(BaseModel):
    # Optional fields
    alert_type: Optional[str] = None
    name: Optional[str] = None
    residential_user_name: Optional[str] = None
    date_updated: Any
    alert_uuid: Optional[str] = None
    state: Optional[str] = None
    date_created: Optional[str] = None
    creator_user_uuid: Optional[str] = None


class Alerts(BaseModel):
    # Optional fields
    leak_alert: Optional[LeakAlert] = None


class AccountInfo(BaseModel):
    # Optional fields
    status: Optional[str] = None
    first_name: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    account_uuid: Optional[str] = None
    billing_address_2: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    portal_status: Optional[str] = None
    last_name: Optional[str] = None
    account_id: Optional[str] = None
    class_code: Optional[str] = None
    billing_address_3: Optional[str] = None
    person_id: Optional[str] = None
    date_created: Optional[str] = None
    account_billing_cycle: Optional[str] = None
    billing_zip_code: Optional[str] = None
    billing_country: Optional[str] = None
    billing_state: Optional[str] = None
    eyeonwater: Optional[str] = None


class SensorsAvailable(BaseModel):
    # Optional fields
    types: Optional[list[str]] = None


class Battery(BaseModel):
    # Optional fields
    register_: Optional[int] = Field(None, alias="register")
    level: Optional[int] = None
    quality: Optional[str] = None
    thresh12mo: Optional[int] = None
    time: Optional[datetime] = None


class Pwr(BaseModel):
    # Optional fields
    level: Optional[int] = None
    register_: Optional[int] = Field(None, alias="register")
    signal_7days: Optional[int] = None
    signal_strength: Optional[int] = None
    time: Optional[datetime] = None
    quality: Optional[str] = None
    signal_30days: Optional[int] = None


class Notes(BaseModel):
    # Optional fields
    count: Optional[int] = None


class Flow(BaseModel):
    # Optional fields
    this_week: Optional[float] = None
    months_updated: Optional[str] = None
    last_month: Optional[float] = None
    last_year_last_month_ratio: Optional[float] = None
    last_year_last_month: Optional[float] = None
    delta_positive: Optional[float] = None
    time: Optional[datetime] = None
    time_positive: Optional[str] = None
    last_month_ratio: Optional[float] = None
    last_week_avg: Optional[float] = None
    last_year_this_month_ratio: Optional[float] = None
    delta: Optional[float] = None
    this_month: Optional[float] = None
    week_ratio: Optional[float] = None
    weeks_updated: Optional[str] = None
    last_year_this_month: Optional[float] = None
    last_week: Optional[float] = None
    this_week_avg: Optional[float] = None


class ActiveFlags(BaseModel):
    # Optional fields
    active_flags: Optional[list[str]] = None
    time: Optional[datetime] = None


class MeterData(BaseModel):
    # Optional fields
    sensors_available: Optional[SensorsAvailable] = None
    has_endpoint: Optional[bool] = None
    install_date: Optional[datetime] = None
    meter_uuid: Optional[str] = None
    fluid_type: Optional[str] = None
    timezone: Optional[str] = None
    firmware_version: Optional[str] = None
    communication_security: Optional[str] = None
    meter_size_unit: Optional[str] = None
    cell_type: Optional[str] = None
    geocode_status: Optional[int] = None
    geo: Optional[str] = None
    last_read_time: Optional[datetime] = None
    note: Optional[str] = None
    battery: Optional[Battery] = None
    endpoint_status: Optional[str] = None
    alert_code: Optional[int] = None
    gas_pressure_compensation: Optional[float] = None
    service_type: Optional[str] = None
    serial_number: Optional[str] = None
    type_: Optional[str] = Field(None, alias="type")
    pwr: Optional[Pwr] = None
    endpoint_connector: Optional[str] = None
    communication_seconds: Optional[int] = None
    meter_size_desc: Optional[str] = None
    is_compound: Optional[str] = None
    latitude: Optional[str] = None
    typical_read_method: Optional[str] = None
    endpoint_type: Optional[str] = None
    meter_id: Optional[str] = None
    last_communication_time: Optional[datetime] = None
    pit_type: Optional[str] = None
    meter_spec_uuid: Optional[str] = None
    manufacturer: Optional[str] = None
    has_valve: Optional[bool] = None
    has_sensor: Optional[bool] = None
    gas_sub_count: Optional[int] = None
    notes: Optional[Notes] = None
    meter_size: Optional[float] = None
    flow: Optional[Flow] = None
    longitude: Optional[str] = None
    flags: Optional[ActiveFlags] = None
    model: Optional[str] = None
    sequence_number: Optional[int] = None


class ServiceAgreement(BaseModel):
    # Optional fields
    service_agreement_uuid: Optional[str] = None
    start_date: Optional[datetime] = None


class LatestRead(BaseModel):
    # Mandatory fields
    full_read: float
    units: EOWUnits

    # Optional fields
    bill_read: Optional[float] = None
    bill_display_units: Optional[EOWUnits] = None
    read_time: datetime
    has_endpoints: Optional[bool] = None
    method: Optional[str] = None


class Timeslots(BaseModel):
    # Optional fields
    weekend: Optional[list[int]] = None
    weekday: Optional[list[int]] = None


class Encoder(BaseModel):
    # Optional fields
    time: Optional[datetime] = None
    dials: Optional[int] = None
    register_id: Optional[str] = None
    totalizer: Optional[int] = None


class Flags(BaseModel):
    # Mandatory fields (used by EOW HA integration)
    empty_pipe: bool = Field(..., alias="EmptyPipe")
    leak: bool = Field(..., alias="Leak")
    cover_removed: bool = Field(..., alias="CoverRemoved")
    tamper: bool = Field(..., alias="Tamper")
    reverse_flow: bool = Field(..., alias="ReverseFlow")
    low_battery: bool = Field(..., alias="LowBattery")
    battery_charging: bool = Field(..., alias="BatteryCharging")

    # Optional fields
    forced: Optional[bool] = Field(None, alias="Forced")
    magnetic_tamper: Optional[bool] = Field(None, alias="MagneticTamper")
    encoder_no_usage: Optional[bool] = Field(None, alias="EncoderNoUsage")
    encoder_temperature: Optional[bool] = Field(None, alias="EncoderTemperature")
    encoder_reverse_flow: Optional[bool] = Field(None, alias="EncoderReverseFlow")
    reading_changed: Optional[bool] = Field(None, alias="ReadingChanged")
    programming_changed: Optional[bool] = Field(None, alias="ProgrammingChanged")
    encoder_exceeding_max_flow: Optional[bool] = Field(
        None, alias="EncoderExceedingMaxFlow"
    )
    water_temperature_sensor_error: Optional[bool] = Field(
        None, alias="WaterTemperatureSensorError"
    )
    oscillator_failure: Optional[bool] = Field(None, alias="OscillatorFailure")
    encoder_sensor_error: Optional[bool] = Field(None, alias="EncoderSensorError")
    encoder_leak: Optional[bool] = Field(None, alias="EncoderLeak")
    water_pressure_sensor_error: Optional[bool] = Field(
        None, alias="WaterPressureSensorError"
    )
    min_max_invalid: Optional[bool] = Field(None, alias="MinMaxInvalid")
    end_of_life: Optional[bool] = Field(None, alias="EndOfLife")
    encoder_dial_change: Optional[bool] = Field(None, alias="EncoderDialChange")
    no_usage: Optional[bool] = Field(None, alias="NoUsage")
    device_alert: Optional[bool] = Field(None, alias="DeviceAlert")
    endpoint_reading_missed: Optional[bool] = Field(None, alias="EndpointReadingMissed")
    encoder_removal: Optional[bool] = Field(None, alias="EncoderRemoval")
    profile_read_error: Optional[bool] = Field(None, alias="ProfileReadError")
    encoder_programmed: Optional[bool] = Field(None, alias="EncoderProgrammed")
    time: Optional[datetime] = None
    encoder_magnetic_tamper: Optional[bool] = Field(None, alias="EncoderMagneticTamper")
    meter_temperature_sensor_error: Optional[bool] = Field(
        None, alias="MeterTemperatureSensorError"
    )


class Reading(BaseModel):
    # Mandatory fields
    flags: Flags
    latest_read: LatestRead

    # Optional fields
    battery: Optional[Battery] = None
    customer_uuid: Optional[str] = None
    aggregation_seconds: Optional[int] = None
    last_communication_time: Optional[datetime] = None
    firmware_version: Optional[str] = None
    communication_security: Optional[str] = None
    meter_size_desc: Optional[str] = None
    barnacle_uuid: Optional[str] = None
    unit: Optional[EOWUnits] = None
    customer_name: Optional[str] = None
    cell_type: Optional[str] = None
    pi_status: Optional[str] = None
    second_carrier: Optional[bool] = None
    input_config: Optional[str] = None
    meter_size_unit: Optional[str] = None
    endpoint_status: Optional[str] = None
    gas_pressure_compensation: Optional[float] = None
    serial_number: Optional[str] = None
    activated_on: Optional[str] = None
    sim_vendor: Optional[str] = None
    pwr: Optional[Pwr] = None
    communication_seconds: Optional[int] = None
    cell_endpoint_name: Optional[str] = None
    rf_communication: Optional[bool] = None
    low_read_limit: Optional[int]
    utility_use_1: Optional[str] = None
    timeslots: Optional[Timeslots] = None
    encoder: Optional[Encoder] = None
    endpoint_type: Optional[str] = None
    utility_use_2: Optional[str] = None
    multiplier: Optional[str] = None
    sim_type: Optional[str] = None
    register_number: Optional[str] = None
    wired_interface: Optional[str] = None
    endpoint_install_date: Optional[datetime] = None
    high_read_limit: Optional[int] = None
    gas_sub_count: Optional[int] = None
    billing_number: Optional[str] = None
    meter_size: Optional[float] = None
    flow: Optional[Flow] = None
    hardware_version: Optional[str] = None
    connector_type: Optional[str] = None
    model: Optional[str] = None
    resolution: Optional[float] = None


class Conditions(BaseModel):
    # Optional fields
    increasing: Optional[bool] = None
    decreasing: Optional[bool] = None


class EndpointTemperature(BaseModel):
    # Optional fields
    latest_average: Optional[float] = None
    last_reported: Optional[str] = None
    seven_day_min: Optional[float] = None
    seven_day_average: Optional[float] = None
    seven_day_max: Optional[float] = None
    sensor_uuid: Optional[str] = None
    conditions: Optional[Conditions] = None


class Sensors(BaseModel):
    # Optional fields
    endpoint_temperature: Optional[EndpointTemperature] = None


class Utility(BaseModel):
    # Optional fields
    fluid_barrel_billing_unit: Optional[str] = None
    cm_billing_unit: Optional[str] = None
    cf_billing_unit: Optional[str] = None
    type_: Optional[str] = Field(None, alias="type")
    utility_name: Optional[str] = None
    eow_service_selector: Optional[str] = None
    gas_cf_billing_unit: Optional[str] = None
    eow_type: Optional[str] = None
    oil_barrel_billing_unit: Optional[str] = None
    date_created: Optional[str] = None
    gal_billing_unit: Optional[str] = None
    gas_cm_billing_unit: Optional[str] = None
    utility_uuid: Optional[str] = None
    imp_billing_unit: Optional[str] = None


class User(BaseModel):
    # Optional fields
    user_uuid: Optional[str] = None
    user_name: Optional[str] = None
    date_created: Optional[str] = None


class Groups(BaseModel):
    # Optional fields
    irrigation: Optional[str] = None
    continuous_flow: Optional[str] = None
    is_irrigatable: Optional[str] = None
    disable_valve_shutoff: Optional[str] = None


class MeterInfo(BaseModel):
    # Mandatory fields
    reading: Reading = Field(..., alias="register_0")

    # Optional fields
    sensors: Optional[Sensors] = None
    utility: Optional[Utility] = None
    updated: Optional[int] = None
    last_updated: Optional[str] = None
    service: Optional[Service] = None
    location: Optional[Location] = None
    alerts: Optional[Alerts] = None
    account: Optional[AccountInfo] = None
    meter: Optional[MeterData] = None
    service_agreement: Optional[ServiceAgreement] = None
    version: Optional[str] = None
    user: Optional[User] = None
    groups: Optional[Groups] = None
