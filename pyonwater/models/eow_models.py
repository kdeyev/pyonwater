# ruff: noqa

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .units import EOWUnits


class Service(BaseModel):
    class_code_normalized: str
    route: str
    active: bool
    class_code: str
    service_type: str
    service_id: str
    start_date: datetime
    service_point_uuid: str
    cycle: str


class Location(BaseModel):
    city: str
    parcel_number: str
    location_name: str
    parity: str
    country: str
    route: str
    geocode_status: int
    zip_code: str
    longitude: str
    display_address_3: str
    state: str
    location_uuid: str
    county_name: str
    latitude: str
    display_address_2: str
    location_id: str
    display_address: str
    display_street_name: str
    cycle: str


class LeakAlert(BaseModel):
    alert_type: str
    name: str
    residential_user_name: str
    date_updated: Any
    alert_uuid: str
    state: str
    date_created: str
    creator_user_uuid: str


class Alerts(BaseModel):
    leak_alert: LeakAlert


class AccountInfo(BaseModel):
    status: str
    first_name: str
    billing_address: str
    billing_city: str
    account_uuid: str
    billing_address_2: str
    full_name: str
    email: str
    phone: str
    portal_status: str
    last_name: str
    account_id: str
    class_code: str
    billing_address_3: str
    person_id: str
    date_created: str
    account_billing_cycle: str
    billing_zip_code: str
    billing_country: str
    billing_state: str
    eyeonwater: str


class SensorsAvailable(BaseModel):
    types: list[str]


class Battery(BaseModel):
    register_: int = Field(..., alias="register")
    level: int
    quality: str
    thresh12mo: int
    time: datetime


class Pwr(BaseModel):
    level: int
    register_: int = Field(..., alias="register")
    signal_7days: int
    signal_strength: int
    time: datetime
    quality: str
    signal_30days: int


class Notes(BaseModel):
    count: int


class Flow(BaseModel):
    this_week: float
    months_updated: str
    last_month: float
    last_year_last_month_ratio: float
    last_year_last_month: float
    delta_positive: float
    time: datetime
    time_positive: str
    last_month_ratio: float
    last_week_avg: float
    last_year_this_month_ratio: float
    delta: float
    this_month: float
    week_ratio: float
    weeks_updated: str
    last_year_this_month: float
    last_week: float
    this_week_avg: float


class ActiveFlags(BaseModel):
    active_flags: list[str]
    time: datetime


class MeterData(BaseModel):
    sensors_available: SensorsAvailable
    has_endpoint: bool
    install_date: datetime
    meter_uuid: str
    fluid_type: str
    timezone: str
    firmware_version: str
    communication_security: str
    meter_size_unit: str
    cell_type: str
    geocode_status: int
    geo: str
    last_read_time: datetime
    note: str
    battery: Battery
    endpoint_status: str
    alert_code: int
    gas_pressure_compensation: float
    service_type: str
    serial_number: str
    type_: str = Field(..., alias="type")
    pwr: Pwr
    endpoint_connector: str
    communication_seconds: int
    meter_size_desc: str
    is_compound: str
    latitude: str
    typical_read_method: str
    endpoint_type: str
    meter_id: str
    last_communication_time: datetime
    pit_type: str
    meter_spec_uuid: str
    manufacturer: str
    has_valve: bool
    has_sensor: bool
    gas_sub_count: int
    notes: Notes
    meter_size: float
    flow: Flow
    longitude: str
    flags: ActiveFlags
    model: str
    sequence_number: int


class ServiceAgreement(BaseModel):
    service_agreement_uuid: str
    start_date: datetime


class LatestRead(BaseModel):
    bill_read: str
    bill_display_units: EOWUnits
    full_read: float
    read_time: datetime
    has_endpoints: bool
    units: EOWUnits
    method: str


class Timeslots(BaseModel):
    weekend: list[int]
    weekday: list[int]


class Encoder(BaseModel):
    time: datetime
    dials: int
    register_id: str
    totalizer: int


class Flags(BaseModel):
    forced: bool = Field(..., alias="Forced")
    magnetic_tamper: bool = Field(..., alias="MagneticTamper")
    empty_pipe: bool = Field(..., alias="EmptyPipe")
    leak: bool = Field(..., alias="Leak")
    encoder_no_usage: bool = Field(..., alias="EncoderNoUsage")
    encoder_temperature: bool = Field(..., alias="EncoderTemperature")
    encoder_reverse_flow: bool = Field(..., alias="EncoderReverseFlow")
    reading_changed: bool = Field(..., alias="ReadingChanged")
    cover_removed: bool = Field(..., alias="CoverRemoved")
    programming_changed: bool = Field(..., alias="ProgrammingChanged")
    encoder_exceeding_max_flow: bool = Field(..., alias="EncoderExceedingMaxFlow")
    water_temperature_sensor_error: bool = Field(
        ..., alias="WaterTemperatureSensorError"
    )
    oscillator_failure: bool = Field(..., alias="OscillatorFailure")
    encoder_sensor_error: bool = Field(..., alias="EncoderSensorError")
    tamper: bool = Field(..., alias="Tamper")
    reverse_flow: bool = Field(..., alias="ReverseFlow")
    encoder_leak: bool = Field(..., alias="EncoderLeak")
    low_battery: bool = Field(..., alias="LowBattery")
    water_pressure_sensor_error: bool = Field(..., alias="WaterPressureSensorError")
    min_max_invalid: bool = Field(..., alias="MinMaxInvalid")
    end_of_life: bool = Field(..., alias="EndOfLife")
    encoder_dial_change: bool = Field(..., alias="EncoderDialChange")
    no_usage: bool = Field(..., alias="NoUsage")
    battery_charging: bool = Field(..., alias="BatteryCharging")
    device_alert: bool = Field(..., alias="DeviceAlert")
    endpoint_reading_missed: bool = Field(..., alias="EndpointReadingMissed")
    encoder_removal: bool = Field(..., alias="EncoderRemoval")
    profile_read_error: bool = Field(..., alias="ProfileReadError")
    encoder_programmed: bool = Field(..., alias="EncoderProgrammed")
    time: datetime
    encoder_magnetic_tamper: bool = Field(..., alias="EncoderMagneticTamper")
    meter_temperature_sensor_error: bool = Field(
        ..., alias="MeterTemperatureSensorError"
    )


class Reading(BaseModel):
    battery: Battery
    customer_uuid: str
    aggregation_seconds: int
    last_communication_time: datetime
    firmware_version: str
    communication_security: str
    meter_size_desc: str
    barnacle_uuid: str
    unit: EOWUnits
    customer_name: str
    cell_type: str
    pi_status: str
    second_carrier: bool
    latest_read: LatestRead
    input_config: str
    meter_size_unit: str
    endpoint_status: str
    gas_pressure_compensation: float
    serial_number: str
    activated_on: str
    sim_vendor: str
    pwr: Pwr
    communication_seconds: int
    cell_endpoint_name: str
    rf_communication: bool
    low_read_limit: int
    utility_use_1: str
    timeslots: Timeslots
    encoder: Encoder
    endpoint_type: str
    utility_use_2: str
    multiplier: str
    sim_type: str
    register_number: str
    wired_interface: str
    endpoint_install_date: datetime
    high_read_limit: int
    gas_sub_count: int
    billing_number: str
    meter_size: float
    flow: Flow
    hardware_version: str
    connector_type: str
    flags: Flags
    model: str
    resolution: float


class Conditions(BaseModel):
    increasing: bool
    decreasing: bool


class EndpointTemperature(BaseModel):
    latest_average: float
    last_reported: str
    seven_day_min: str
    seven_day_average: str
    seven_day_max: str
    sensor_uuid: str
    conditions: Conditions


class Sensors(BaseModel):
    endpoint_temperature: EndpointTemperature


class Utility(BaseModel):
    fluid_barrel_billing_unit: str
    cm_billing_unit: str
    cf_billing_unit: str
    type_: str = Field(..., alias="type")
    utility_name: str
    eow_service_selector: str
    gas_cf_billing_unit: str
    eow_type: str
    oil_barrel_billing_unit: str
    date_created: str
    gal_billing_unit: str
    gas_cm_billing_unit: str
    utility_uuid: str
    imp_billing_unit: str


class User(BaseModel):
    user_uuid: str
    user_name: str
    date_created: str


class Groups(BaseModel):
    irrigation: str
    continuous_flow: str
    is_irrigatable: str
    disable_valve_shutoff: str


class MeterInfo(BaseModel):
    reading: Reading = Field(..., alias="register_0")
    sensors: Sensors
    utility: Utility
    updated: int
    last_updated: str
    service: Service
    location: Location
    alerts: Alerts
    account: AccountInfo
    meter: MeterData
    service_agreement: ServiceAgreement
    version: str
    user: User
    groups: Groups
