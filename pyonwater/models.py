from datetime import datetime

from pydantic import BaseModel, Field


class DataPoint(BaseModel):
    dt: datetime
    reading: float


class ReadingDataFlags(BaseModel):
    forced: bool = Field(..., serialization_alias="Forced")
    magneticTamper: bool = Field(..., serialization_alias="MagneticTamper")
    emptyPipe: bool = Field(..., serialization_alias="EmptyPipe")
    leak: bool = Field(..., serialization_alias="Leak")
    forced: bool = Field(..., serialization_alias="Forced")

    # 'EncoderNoUsage': False, 'EncoderTemperature': False, 'EncoderReverseFlow': False, 'ReadingChanged': False, 'CoverRemoved': False, 'ProgrammingChanged': False, 'EncoderExceedingMaxFlow': False, 'WaterTemperatureSensorError': False, 'OscillatorFailure': False, 'EncoderSensorError': False, ...}


class ReadingData(BaseModel):
    flags: ReadingDataFlags


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
