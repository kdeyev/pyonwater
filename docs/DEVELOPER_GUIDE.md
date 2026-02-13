# pyonwater Developer Guide

**Repository:** [kdeyev/pyonwater](https://github.com/kdeyev/pyonwater)  
**Library purpose:** Python async client for the [EyeOnWater](https://eyeonwater.com/) residential water meter API.  

---

## Table of Contents

- [pyonwater Developer Guide](#pyonwater-developer-guide)
  - [Table of Contents](#table-of-contents)
  - [1. EyeOnWater API — Discovery and Key Constraints](#1-eyeonwater-api--discovery-and-key-constraints)
    - [Confirmed Endpoints](#confirmed-endpoints)
      - [Consumption Endpoint Payload](#consumption-endpoint-payload)
      - [Search Endpoint Payload](#search-endpoint-payload)
      - [At-a-Glance Endpoint Payload](#at-a-glance-endpoint-payload)
    - [Discovered but Unimplemented Export Flow](#discovered-but-unimplemented-export-flow)
    - [Aggregation Levels](#aggregation-levels)
    - [Meter Read Frequency](#meter-read-frequency)
  - [2. Library Architecture Overview](#2-library-architecture-overview)
    - [Typical Usage](#typical-usage)
  - [3. AggregationLevel: Enum Subscript vs. Constructor](#3-aggregationlevel-enum-subscript-vs-constructor)
  - [4. Required API Parameters: The `units` Contract](#4-required-api-parameters-the-units-contract)
  - [5. Date Handling: Aggregation-Dependent Formats](#5-date-handling-aggregation-dependent-formats)
  - [6. Data Quality Utilities: `series.py`](#6-data-quality-utilities-seriespy)
    - [`enforce_monotonic_total`](#enforce_monotonic_total)
    - [`filter_points_after`](#filter_points_after)
  - [7. Unit System: Three Distinct Enums](#7-unit-system-three-distinct-enums)
    - [`RequestUnits` — All Valid Values](#requestunits--all-valid-values)
  - [8. Known API Limitations](#8-known-api-limitations)
  - [9. Dependency Notes](#9-dependency-notes)
  - [10. API Validation and Input Guardrails](#10-api-validation-and-input-guardrails)
    - [Protection Layers](#protection-layers)
    - [Test Coverage for API Contracts](#test-coverage-for-api-contracts)
  - [11. Reference Documents](#11-reference-documents)

---

## 1. EyeOnWater API — Discovery and Key Constraints

The EyeOnWater API is **not publicly documented**. The behavior described here was determined empirically through HTTP Archive (HAR) analysis of live browser sessions.

### Confirmed Endpoints

| Endpoint | Method | Purpose |
| -------- | ------ | ------- |
| `/api/2/residential/new_search` | POST | Meter info, latest reading, metadata |
| `/api/2/residential/consumption?eow=True` | POST | Historical time-series data |
| `/api/2/residential/at_a_glance` | POST | Summary card data (this week, last week, etc.) |

#### Consumption Endpoint Payload

```python
{
    "params": {
        "source": "barnacle",                # Fixed — REQUIRED
        "aggregate": aggregation.value,      # AggregationLevel value — REQUIRED
        "units": units.value or "cm",        # Always send — REQUIRED (silent fail if omitted)
        "perspective": "billing",            # Fixed — REQUIRED
        "combine": "true",                   # Fixed — REQUIRED
        "date": date.strftime("%m/%d/%Y"),   # End date in MM/DD/YYYY — REQUIRED
        "display_minutes": True,             # Fixed — REQUIRED
        "display_hours": True,               # Fixed — REQUIRED
        "display_days": True,                # Fixed — REQUIRED
        "display_weeks": True,               # Fixed — REQUIRED
        "furthest_zoom": "hr",               # Fixed — REQUIRED
    },
    "query": {
        "query": {
            "terms": {
                "meter.meter_uuid": ["<uuid>"]   # REQUIRED — array with exactly one UUID
            }
        }
    }
}
```

#### Search Endpoint Payload

```python
{
    "query": {
        "terms": {
            "meter.meter_uuid": ["<uuid>"]   # REQUIRED
        }
    }
}
```

#### At-a-Glance Endpoint Payload

```python
{
    "params": {
        "source": "barnacle",
        "perspective": "billing",
        "units": units.value or "cm",        # Defaulted for safety
    },
    "query": {
        "query": {
            "terms": {
                "meter.meter_uuid": ["<uuid>"]
            }
        }
    }
}
```

### Discovered but Unimplemented Export Flow

HAR analysis of live browser sessions revealed a CSV export flow not currently implemented in pyonwater. These endpoints are available in the EyeOnWater web UI but have not been reverse-engineered into the library:

| Endpoint | Method | Purpose |
| -------- | ------ | ------- |
| (initiate — path not fully captured) | GET/POST | Starts async export job, returns `task_id` |
| `/reports/export_check_status/task:{task_id}` | GET | Polls job completion |
| `/reports/export_stored_status` | GET | Lists available stored exports |
| (S3 redirect) | GET | Downloads the CSV file |

The export CSV provides raw metered readings independent of aggregation level and was used as ground truth during API validation. Implementing this flow would allow sub-hourly data collection without relying on the `consumption` endpoint.

> See [EYE_ON_WATER_API_RESEARCH.md](./EYE_ON_WATER_API_RESEARCH.md) for the full HAR analysis session log.

### Aggregation Levels

The `aggregate` parameter controls time bucket size. The API values do **not** match intuitive names:

| `AggregationLevel` enum | API string value | Actual resolution | Notes |
| ---------------------- | --------------- | ----------------- | ----- |
| `QUARTER_HOURLY` | `"hr"` | 15-minute intervals | Named `hr` despite being 15-min |
| `HOURLY` | `"hourly"` | 1-hour intervals | Recommended for statistics import |
| `DAILY` | `"daily"` | Calendar day | |
| `WEEKLY` | `"weekly"` | 7-day intervals | |
| `MONTHLY` | `"monthly"` | Calendar month | Returns `YYYY-MM` dates — see §5 |
| `YEARLY` | `"yearly"` | Calendar year | |

**Tested but not supported:**

| Attempted value | Result |
| --------------- | ------ |
| `"quarter_hourly"` | HTTP 200 + empty body |
| `"15_min"` | HTTP 200 + empty body |
| `"15min"` | HTTP 200 + empty body |

The meter hardware reports every 15 minutes (`read_frequency: "15 Minutes"` from the embedded page source), but the consumption API does not expose sub-hourly data via the standard endpoint.

### Meter Read Frequency

The meter hardware transmits readings every 15 minutes. This is visible in the dashboard page source:

```javascript
var new_barInfo = {
  "read_frequency": "15 Minutes",
  "next_update": [{"new_comms_date": "...", "new_comms_time": "..."}]
}
```

This 15-minute cadence is relevant to the eyeonwater coordinator polling interval, but the finest granularity available from the consumption API is `HOURLY`.

---

## 2. Library Architecture Overview

```text
pyonwater/
├── account.py          Account discovery and meter enumeration
├── client.py           Async HTTP session management (aiohttp)
├── meter.py            Meter entity — wraps MeterReader, holds last_historical_data
├── meter_reader.py     Direct API calls: read_meter_info(), read_historical_data()
├── series.py           Data quality utilities: enforce_monotonic_total(), filter_points_after()
├── units.py            Unit conversion: convert_to_native(), deduce_native_units()
└── models/
    ├── eow_models.py           Pydantic models: MeterInfo, DataPoint, HistoricalData, etc.
    ├── eow_historical_models.py Pydantic models for historical API responses (Series, Params, etc.)
    └── units.py                Enums: EOWUnits, NativeUnits, RequestUnits, AggregationLevel
```

### Typical Usage

```python
from pyonwater import Account, Client, AggregationLevel

# 1. Authenticate
account = Account(username="user@example.com", password="secret", eow_hostname="eyeonwater.com")
async with aiohttp.ClientSession() as session:
    client = Client(session, account)
    await account.fetch_auth(client)

    # 2. Discover meters
    meters = await account.fetch_meters(client)

    for meter in meters:
        # 3. Read current state
        meter_info = await meter.read_meter_info(client)

        # 4. Read historical data (last 7 days, hourly)
        points = await meter.read_historical_data(
            client,
            days_to_load=7,
            aggregation=AggregationLevel.HOURLY,
        )
        # points: list[DataPoint], each has .dt (datetime) and .reading (float)
```

---

## 3. AggregationLevel: Enum Subscript vs. Constructor

**This is the single most common integration mistake.**

`AggregationLevel` is a `str` enum. The enum *values* are the API strings (`"hourly"`, `"daily"`, etc.). The enum *names* are the Python constants (`HOURLY`, `DAILY`, etc.).

```python
from pyonwater import AggregationLevel

# CORRECT — subscript by name
level = AggregationLevel["HOURLY"]   # → AggregationLevel.HOURLY (value="hourly")

# WRONG — calling the constructor with the name
level = AggregationLevel("HOURLY")   # → raises ValueError: 'HOURLY' is not a valid AggregationLevel

# Also correct — calling the constructor with the API value
level = AggregationLevel("hourly")   # → AggregationLevel.HOURLY
```

This matters when the aggregation level is passed as a string from external configuration (e.g., a Home Assistant service call receiving `"HOURLY"` as text). Always use the subscript form (`AggregationLevel["HOURLY"]`) when the input is the enum name.

---

## 4. Required API Parameters: The `units` Contract

The consumption endpoint (`/api/2/residential/consumption?eow=True`) silently returns an empty response if **any** required parameter is missing. There is no error code, no HTTP error, and no exception raised — the response is simply `""`.

**Required parameters (all must be present):**

| Parameter | Value | Type | Notes |
| --------- | ----- | ---- | ----- |
| `source` | `"barnacle"` | Hardcoded | Fixed — cannot vary |
| `aggregate` | `AggregationLevel` value | Enum | e.g. `"hourly"`, `"daily"` |
| `units` | `RequestUnits` value or `"cm"` | **CRITICAL** | Silent empty response if omitted |
| `perspective` | `"billing"` | Hardcoded | Fixed |
| `combine` | `"true"` | Hardcoded | Fixed |
| `date` | `MM/DD/YYYY` | datetime via `strftime` | End date of the requested range |
| `display_minutes` | `True` | Hardcoded | Fixed boolean |
| `display_hours` | `True` | Hardcoded | Fixed boolean |
| `display_days` | `True` | Hardcoded | Fixed boolean |
| `display_weeks` | `True` | Hardcoded | Fixed boolean |
| `furthest_zoom` | `"hr"` | Hardcoded | Fixed |

The `units` parameter in particular is dangerous to omit because it is **optional-looking** (the API accepts requests without it, but returns empty data). The constant `DEFAULT_REQUEST_UNITS = "cm"` is defined in `meter_reader.py` and used as the unconditional fallback:

```python
# meter_reader.py
DEFAULT_REQUEST_UNITS = "cm"  # Always sent; never conditional
```

> **Historical note:** A 2026 refactor (PR #36) made `units` conditional on user preference. All requests where `units=None` started returning empty data. The fix restores `units` as unconditional with `DEFAULT_REQUEST_UNITS` as fallback. Any future refactor that touches this parameter must maintain the always-sent invariant.

---

## 5. Date Handling: Aggregation-Dependent Formats

The EyeOnWater API returns dates in different formats depending on the aggregation level:

| Aggregation | Date format returned | Example |
| ----------- | ------------------- | ------- |
| Quarter-hourly / Hourly / Daily / Weekly | `YYYY-MM-DD HH:MM:SS` | `"2026-02-14 15:00:00"` |
| Monthly | `YYYY-MM` | `"2026-02"` |
| Yearly | `YYYY` | `"2026"` |

The `Series.date` field in `eow_historical_models.py` uses a custom `parse_flexible_date` validator to handle this variance:

```python
@field_validator("date", mode="before")
@classmethod
def parse_flexible_date(cls, v: Any) -> datetime:
    """Parse date from various formats depending on API aggregation level."""
    if isinstance(v, datetime):
        return v                         # Already parsed by pydantic — pass through
    for fmt in DATE_FORMATS:            # Includes "%Y-%m-%d %H:%M:%S" and "%Y-%m"
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {v!r}")
```

**Key implementation note:** The validator signature uses `v: Any` (not `v: str`). Pydantic's `mode="before"` validator can receive an already-parsed `datetime` object during model revalidation. A `str`-typed signature would raise a `TypeError` in that case. The `isinstance(v, datetime)` guard handles the early-return path.

---

## 6. Data Quality Utilities: `series.py`

The EyeOnWater API occasionally returns readings that violate physical expectations of a cumulative water meter. The `series.py` module provides two utilities to correct this before the data reaches downstream consumers.

### `enforce_monotonic_total`

Clamps any reading that is lower than the previous to the previous value. This handles:

- Float precision artifacts (e.g., `199,975.0` followed by `199,974.98`)
- Meter rollback events (rare but observed)

```python
from pyonwater import enforce_monotonic_total

points = await meter.read_historical_data(client, days_to_load=7)
clean = enforce_monotonic_total(points, clamp_min=0.0)
# clean: same length, all readings ≥ previous reading
```

The `clamp_min` parameter optionally enforces a floor value (pass `0.0` to prevent negative readings). If `None` (the default), only the monotonic constraint is applied.

**Why this matters for statistics import:** Home Assistant's long-term statistics pipeline uses successive `sum` values. A backward step in the source data produces a negative consumption bar in the Energy Dashboard. Clamping eliminates these before they enter the statistics table.

### `filter_points_after`

Returns only points with `.dt > since`, used to avoid re-importing readings that are already in the statistics database.

```python
from pyonwater import filter_points_after

# Get last imported time from the statistics DB (handled by eyeonwater's statistic_helper)
new_points = filter_points_after(points, since=last_imported_datetime)
```

If `since=None`, all points are returned unchanged.

---

## 7. Unit System: Three Distinct Enums

pyonwater has three different unit enums that serve different purposes. Using the wrong one in the wrong context causes silent failures.

| Enum | Location | Used for | Example values |
| ---- | -------- | -------- | -------------- |
| `RequestUnits` | `models/units.py` | `units=` parameter in API requests | `"cm"`, `"gallons"`, `"cf"` |
| `EOWUnits` | `models/units.py` | Unit strings in API response bodies | `"GAL"`, `"CM"`, `"CUBIC_FEET"` |
| `NativeUnits` | `models/units.py` | Normalized unit for `DataPoint.unit` | `"gal"`, `"cm"`, `"cf"` |

### `RequestUnits` — All Valid Values

These are the only values the EyeOnWater API accepts for the `units` request parameter, validated empirically from HAR analysis:

| Enum member | String value | Description |
| ----------- | ------------ | ----------- |
| `RequestUnits.GALLONS` | `"gallons"` | US gallons |
| `RequestUnits.CUBIC_FEET` | `"cf"` | Cubic feet |
| `RequestUnits.CCF` | `"ccf"` | Centum cubic feet (100 ft³) |
| `RequestUnits.LITERS` | `"liters"` | Liters |
| `RequestUnits.CUBIC_METERS` | `"cm"` | Cubic meters ⭐ **DEFAULT** |
| `RequestUnits.IMPERIAL_GALLONS` | `"imp"` | Imperial gallons |
| `RequestUnits.OIL_BARRELS` | `"oil_barrel"` | Oil barrels |
| `RequestUnits.FLUID_BARRELS` | `"fluid_barrel"` | Fluid barrels |

The `"cm"` (cubic meters) default is used unconditionally when `units=None` is passed to avoid silent empty-response failures (see §4).

The `units.py` module provides `convert_to_native()` and `deduce_native_units()` to translate between the response units (`EOWUnits`) and the normalized form (`NativeUnits`) used internally.

**Home Assistant consumer note:** When building `StatisticMetaData`, the `unit_of_measurement` field must receive the string value of a `UnitOfVolume` enum (e.g., `"gal"`, `"ft³"`, `"m³"`). Passing a `UnitOfVolume` enum object directly causes HA's recorder to silently reject all statistics inserts for that metadata ID. Use `.value` explicitly:

```python
# In eyeonwater/statistic_helper.py:
unit_of_measurement=get_ha_native_unit_of_measurement(unit_enum).value  # ".value" is required
```

---

## 8. Known API Limitations

| Limitation | Description | Current handling |
| ---------- | ----------- | ---------------- |
| No sub-hourly data via consumption endpoint | `quarter_hourly` returns empty body | `AggregationLevel.HOURLY` used for all statistics import |
| Monthly dates use `YYYY-MM` format | Pydantic v2 rejects by default | `parse_flexible_date` validator handles this |
| Missing `units` returns empty 200 | No error indication | `DEFAULT_REQUEST_UNITS = "cm"` always sent |
| Cross-aggregation overlap | Importing HOURLY and WEEKLY for the same period produces negative bars from data overlap | Restrict to a single aggregation level per import run |
| No incremental endpoint | All historical calls are full date-range requests | `filter_points_after()` deduplicates on the client side |

---

## 9. Dependency Notes

**pydantic:** The library supports both pydantic v1 and v2. The `pyproject.toml` constraint is `pydantic>=1.10.17`. In practice, environments that include Home Assistant will have pydantic v2 installed. All models use the pydantic v2 API (`field_validator`, `model_validate`, `model_dump`, `ConfigDict`).

**Python version:** `>=3.12`. The `str | None` union syntax and `match` statements used throughout require 3.10+; `3.12` is the tested minimum for this branch.

**aiohttp:** All HTTP is async via aiohttp. The `Client` class wraps an externally-provided `aiohttp.ClientSession` — the caller owns the session lifecycle.

---

## 10. API Validation and Input Guardrails

The following table summarizes all input parameters and their current validation status, sourced from `API_VALIDATION.md`:

| Parameter | Status | Validation mechanism | Failure mode if missing |
| --------- | ------ | -------------------- | ----------------------- |
| `meter_uuid` | ✅ Validated | Non-empty string check | Empty API response / error |
| `meter_id` | ✅ Validated | Non-empty string check | Lookup failures |
| `days_to_load` | ✅ Validated | Must be `>= 1` | Invalid date ranges |
| `units` (consumption) | ✅ Validated | Defaults to `"cm"` unconditionally | Empty 200 response |
| `units` (at_a_glance) | ✅ Validated | Defaults to `"cm"` | Potentially empty response |
| `aggregation` | ✅ Type-safe | `AggregationLevel` enum | `ValueError` at construction (prevented) |
| `date` | ⚠️ Partial | Implicit via `datetime.strftime()` | Format error before API call |
| `source` | ✅ Hardcoded | Always `"barnacle"` | Cannot be malformed |
| `perspective` | ✅ Hardcoded | Always `"billing"` | Cannot be malformed |
| `combine` | ✅ Hardcoded | Always `"true"` | Cannot be malformed |

### Protection Layers

1. **Type-safe enums** — `AggregationLevel` and `RequestUnits` prevent invalid values at the Python level.
2. **Unconditional defaults** — `units` is always sent; `DEFAULT_REQUEST_UNITS = "cm"` is the fallback.
3. **Explicit empty-response check** — `EyeOnWaterResponseIsEmpty` is raised before pydantic validation when the API returns `""`.
4. **Pydantic validators** — All response models validate fields on parse, with `parse_flexible_date` handling multi-format dates.

### Test Coverage for API Contracts

| Test file | What it covers |
| --------- | -------------- |
| `test_api_contracts.py` | Required params present in every request payload; regression against parameter omission |
| `test_meter_reader.py` | `EyeOnWaterResponseIsEmpty` raised on empty response; graceful handling |
| `test_units.py` | Enum conversion correctness for all unit types |
| `test_validation.py` | Empty `meter_uuid`, `meter_id`, `days_to_load < 1`, whitespace-only inputs |

> Full validation rationale and payload schemas are documented in [API_VALIDATION.md](./API_VALIDATION.md).

---

## 11. Reference Documents

| Document | Contents |
| -------- | -------- |
| [API_VALIDATION.md](./API_VALIDATION.md) | Full payload schemas, parameter validation table, test coverage |
