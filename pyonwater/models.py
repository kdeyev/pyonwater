from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # @property
    # def extra_fields(self) -> set[str]:
    #     return set(self.__dict__) - set(self.__fields__)


class DataPoint(BaseModel):
    dt: datetime
    reading: float


class ReadingDataFlags(Model):
    forced: bool = Field(..., alias="Forced")
    magneticTamper: bool = Field(..., alias="MagneticTamper")
    emptyPipe: bool = Field(..., alias="EmptyPipe")
    leak: bool = Field(..., alias="Leak")
    tamper: bool = Field(..., alias="Tamper")
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
    min_max_invalid: bool = Field(..., alias="MinMaxInvalid")
    end_of_life: bool = Field(..., alias="EndOfLife")
    encoder_dial_change: bool = Field(..., alias="EncoderDialChange")
    no_usage: bool = Field(..., alias="NoUsage")
    battery_charging: bool = Field(..., alias="BatteryCharging")
    device_alert: bool = Field(..., alias="DeviceAlert")
    encoder_dial_change: bool = Field(..., alias="EncoderDialChange")
    endpoint_reading_missed: bool = Field(..., alias="EndpointReadingMissed")
    encoder_removal: bool = Field(..., alias="EncoderRemoval")
    profile_read_error: bool = Field(..., alias="ProfileReadError")
    encoder_programmed: bool = Field(..., alias="EncoderProgrammed")
    time: datetime = Field(..., alias="time")
    encoder_magnetic_tamper: bool = Field(..., alias="EncoderMagneticTamper")
    meter_temperature_sensor_error: bool = Field(
        ..., alias="MeterTemperatureSensorError"
    )
    encoder_sensor_error: bool = Field(..., alias="EncoderSensorError")
    reverse_flow: bool = Field(..., alias="ReverseFlow")
    encoder_leak: bool = Field(..., alias="EncoderLeak")
    low_battery: bool = Field(..., alias="LowBattery")
    water_pressure_sensor_error: bool = Field(..., alias="WaterPressureSensorError")


class ReadingData(Model):
    flags: ReadingDataFlags


class MeterInfo(Model):
    reading_data: ReadingData = Field(..., alias="register_0")


# 'battery':
# {'register': 0, 'level': 100, 'quality': 'good', 'thresh12mo': 10, 'time': '2023-08-23T02:23:23'}
# 'customer_uuid':
# '5214483767289566908'
# 'aggregation_seconds':
# 900
# 'last_communication_time':
# '2023-08-23T02:23:23'
# 'firmware_version':
# '1.2.295'
# 'communication_security':
# 'Unknown'
# 'meter_size_desc':
# '1"'
# 'barnacle_uuid':
# '5214483767280081463'
# 'unit':
# 'GAL'
# 'register_number':
# 'single'
# 'wired_interface':
# 'encoder'
# 'endpoint_install_date':
# '2020-01-28T05:59:59'
# 'high_read_limit':
# 74000
# 'gas_sub_count':
# 1
# 'billing_number':
# '25891'
# 'meter_size':
# 1.0
# 'flow':
# {'this_week': 4223.8, 'months_updated': '2023-08-22T21:28:33....4113-05:00', 'last_month': 12276.9, 'last_year_last_month_ratio': 0.8230546151548341, 'last_year_last_month': 16068.800000000001, 'delta_positive': 50.0, 'time': '2023-08-23T02:14:59', 'time_positive': '2023-08-23T02:14:59', 'last_month_ratio': 1.0772670625320724, 'last_week_avg': 720.0285714285716, 'last_year_this_month_ratio': 1.1710718554920971, 'delta': 50.0, 'this_month': 13225.5, 'week_ratio': 0.838022300702353, ...}
# 'hardware_version':
# '68781-001.5'
# 'connector_type':
# 'None'
# 'flags':
# {'Forced': False, 'MagneticTamper': False, 'EmptyPipe': False, 'Leak': False, 'EncoderNoUsage': False, 'EncoderTemperature': False, 'EncoderReverseFlow': False, 'ReadingChanged': False, 'CoverRemoved': False, 'ProgrammingChanged': False, 'EncoderExceedingMaxFlow': False, 'WaterTemperatureSensorError': False, 'OscillatorFailure': False, 'EncoderSensorError': False, ...}
# 'model':
# ''
# 'resolution':
# 0.01
