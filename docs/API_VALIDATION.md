# EyeOnWater API Validation and Parameter Requirements

This document catalogs all API endpoints, their parameters, validation requirements, and potential failure modes.

## Summary of Validations

| Parameter | Status | Validation | Failure Mode |
|-----------|--------|------------|--------------|
| `meter_uuid` | ✅ VALIDATED | Must be non-empty string | Empty responses, API errors |
| `meter_id` | ✅ VALIDATED | Must be non-empty string | Lookup failures |
| `days_to_load` | ✅ VALIDATED | Must be >= 1 | Invalid date ranges |
| `units` (consumption) | ✅ VALIDATED | Always defaults to "cm" | Empty API responses |
| `units` (at_a_glance) | ✅ VALIDATED | Always defaults to "cm" | Potentially empty responses |
| `aggregation` | ✅ TYPE-SAFE | AggregationLevel enum | Type errors (prevented by enum) |
| `date` | ⚠️ PARTIAL | Valid datetime object | Format errors (prevented by strftime) |
| `source` | ✅ HARDCODED | Always "barnacle" | Cannot be malformed |
| `perspective` | ✅ HARDCODED | Always "billing" | Cannot be malformed |
| `combine` | ✅ HARDCODED | Always "true" | Cannot be malformed |

## Enum Value Reference

### RequestUnits Enum (For API Requests)

| Enum Name | String Value | Description |
|-----------|-------------|-------------|
| `RequestUnits.GALLONS` | `"gallons"` | US gallons |
| `RequestUnits.CUBIC_FEET` | `"cf"` | Cubic feet |
| `RequestUnits.CCF` | `"ccf"` | Centum cubic feet (100 ft³) |
| `RequestUnits.LITERS` | `"liters"` | Liters |
| `RequestUnits.CUBIC_METERS` | `"cm"` | Cubic meters ⭐ **DEFAULT** |
| `RequestUnits.IMPERIAL_GALLONS` | `"imp"` | Imperial gallons |
| `RequestUnits.OIL_BARRELS` | `"oil_barrel"` | Oil barrels |
| `RequestUnits.FLUID_BARRELS` | `"fluid_barrel"` | Fluid barrels |

**Note:** When `units=None` is passed, the code defaults to `"cm"` (cubic meters) to prevent empty API responses.

### AggregationLevel Enum (Time Granularity)

| Enum Name | String Value | Interval | Description |
|-----------|-------------|----------|-------------|
| `AggregationLevel.QUARTER_HOURLY` | `"hr"` | 15 minutes | 15-minute intervals |
| `AggregationLevel.HOURLY` | `"hourly"` | 1 hour | 1-hour intervals ⭐ **DEFAULT** |
| `AggregationLevel.DAILY` | `"daily"` | 1 day | 1-day intervals |
| `AggregationLevel.WEEKLY` | `"weekly"` | 7 days | 7-day intervals |
| `AggregationLevel.MONTHLY` | `"monthly"` | 1 month | 1-month intervals |
| `AggregationLevel.YEARLY` | `"yearly"` | 1 year | 1-year intervals |

**Note:** The aggregation parameter has a default value of `AggregationLevel.HOURLY`, so it is never None.

## API Endpoints

### 1. Consumption API - `/api/2/residential/consumption`

**Method:** POST  
**Purpose:** Retrieve historical water consumption data

#### Request Payload Structure
```python
{
    "params": {
        "source": str,           # REQUIRED - Must be "barnacle"
        "aggregate": str,        # REQUIRED - Aggregation level
        "units": str,            # REQUIRED - Unit type (empty → empty response!)
        "perspective": str,      # REQUIRED - Must be "billing"
        "combine": str,          # REQUIRED - Must be "true"
        "date": str,             # REQUIRED - Format: MM/DD/YYYY
        "display_minutes": bool, # Boolean flag
        "display_hours": bool,   # Boolean flag
        "display_days": bool,    # Boolean flag
        "display_weeks": bool,   # Boolean flag
        "furthest_zoom": str     # Typically "hr"
    },
    "query": {
        "query": {
            "terms": {
                "meter.meter_uuid": [str]  # REQUIRED - Array with meter UUID
            }
        }
    }
}
```

#### Mandatory Parameters

| Parameter | Value Type | Validation | Default | Can be Empty? | Notes |
|-----------|------------|------------|---------|---------------|-------|
| `source` | `str` | Hardcoded | `"barnacle"` | ❌ No | Fixed value, cannot be configured |
| `aggregate` | `str` | Enum | - | ❌ No | From `AggregationLevel` enum |
| `units` | `str` | Enum | `"cm"` | ❌ **CRITICAL** | Missing causes empty response |
| `perspective` | `str` | Hardcoded | `"billing"` | ❌ No | Fixed value |
| `combine` | `str` | Hardcoded | `"true"` | ❌ No | Fixed value |
| `date` | `str` | Format | - | ❌ No | Must be MM/DD/YYYY format |
| `meter.meter_uuid` | `list[str]` | Non-empty | - | ❌ No | Must contain valid UUID |

#### Parameterized Fields

| Field | Type | Enum | Current Validation | Potential Issues |
|-------|------|------|-------------------|------------------|
| `aggregate` | Required | `AggregationLevel` | ✅ Type-safe enum | Invalid values prevented by enum |
| `units` | Required | `RequestUnits` | ✅ Defaults to "cm" | Missing parameter → empty API response |
| `date` | Required | N/A | ⚠️ Implicit via `strftime` | Invalid datetime would raise exception |
| `meter_uuid` | Required | N/A | ✅ Non-empty validation | Empty string → API errors |

#### API Behavior

- **Missing `units`**: Returns empty string `""` (silent failure)
- **Missing other params**: Returns empty string `""` (silent failure)
- **Invalid `meter_uuid`**: Returns empty results or error
- **Invalid `date`**: Returns empty results
- **Invalid `aggregate`**: Prevented by type-safe enum validation

### 2. Search API - `/api/2/residential/new_search`

**Method:** POST  
**Purpose:** Get current meter reading and metadata

#### Request Payload Structure
```python
{
    "query": {
        "terms": {
            "meter.meter_uuid": [str]  # REQUIRED
        }
    }
}
```

#### Mandatory Parameters

| Parameter | Value Type | Validation | Can be Empty? | Notes |
|-----------|------------|------------|---------------|-------|
| `meter.meter_uuid` | `list[str]` | Non-empty | ❌ No | Must be valid UUID |

#### API Behavior

- **Missing `meter_uuid`**: API error or empty results
- **Invalid `meter_uuid`**: Empty `hits` array
- **Multiple results**: Raises `EyeOnWaterAPIError`

### 3. At-a-Glance API - `/api/2/residential/at_a_glance`

**Method:** POST  
**Purpose:** Get quick summary statistics (this week, last week, average)

#### Request Payload Structure
```python
{
    "params": {
        "source": str,       # REQUIRED - Must be "barnacle"
        "perspective": str,  # REQUIRED - Must be "billing"
        "units": str         # Optional? (now defaulted for safety)
    },
    "query": {
        "query": {
            "terms": {
                "meter.meter_uuid": [str]  # REQUIRED
            }
        }
    }
}
```

#### Mandatory Parameters

| Parameter | Value Type | Validation | Default | Can be Empty? | Notes |
|-----------|------------|------------|---------|---------------|-------|
| `source` | `str` | Hardcoded | `"barnacle"` | ❌ No | Fixed value |
| `perspective` | `str` | Hardcoded | `"billing"` | ❌ No | Fixed value |
| `units` | `str` | Enum | `"cm"` | ⚠️ Unknown | Now defaulted for consistency |
| `meter.meter_uuid` | `list[str]` | Non-empty | - | ❌ No | Must be valid UUID |

#### API Behavior

- **Missing `units`**: Unknown if causes empty response (defaulted for safety)
- **Missing `source`/`perspective`**: Likely empty response
- **Invalid `meter_uuid`**: Returns error or invalid data

## Validation Strategy

### Current Protection Mechanisms

1. **Type Safety (Enums)**
   - `AggregationLevel`: Ensures only valid aggregation levels
   - `RequestUnits`: Ensures only valid unit types
   - `NativeUnits`, `EOWUnits`: Response validation

2. **Default Values**
   - `units`: Always defaults to `"cm"` in consumption API ✅
   - `units`: Now defaults to `"cm"` in at_a_glance API ✅
   - `aggregation`: Defaults to `AggregationLevel.HOURLY` ✅

3. **Input Validation**
   - `meter_uuid`: Must be non-empty string ✅
   - `meter_id`: Must be non-empty string ✅
   - `days_to_load`: Must be >= 1 ✅

4. **Hardcoded Values** (Cannot be malformed)
   - `source`: Always `"barnacle"`
   - `perspective`: Always `"billing"`
   - `combine`: Always `"true"`
   - Display flags: Always `True`
   - `furthest_zoom`: Always `"hr"`

### Remaining Risks

1. **Date Validation** ⚠️
   - Currently implicit via `datetime.strftime()`
   - Invalid datetime object would raise exception before API call
   - **Risk**: Low (Python datetime handles this)
   - **Recommendation**: Current approach sufficient

2. **Empty Response Handling** ✅
   - Added explicit check for empty API responses
   - Raises `EyeOnWaterResponseIsEmpty` exception
   - Logged with warning in batch operations

3. **Pydantic Validation** ✅
   - All API responses validated via Pydantic models
   - Catches unexpected response formats
   - Provides clear error messages

## Test Coverage

### Current Tests

1. **API Contract Tests** (`test_api_contracts.py`)
   - ✅ Validates all required parameters in request payload
   - ✅ Mock endpoints validate required params and return empty if missing
   - ✅ Prevents parameter-related regressions

2. **Empty Response Tests** (`test_meter_reader.py`)
   - ✅ Tests `test_meter_reader_empty_response`
   - ✅ Validates graceful handling of empty API responses

3. **Unit Tests** (`test_units.py`)
   - ✅ Validates enum conversions
   - ✅ Tests all unit types

4. **Input Validation Tests** (`test_validation.py`)
   - ✅ Empty `meter_uuid` → `ValueError`
   - ✅ Empty `meter_id` → `ValueError`
   - ✅ `days_to_load < 1` → `ValueError`
   - ✅ `days_to_load = 0` → `ValueError`
   - ✅ Whitespace-only inputs → `ValueError`
   - ✅ Enum validation tests for `AggregationLevel` and `RequestUnits`

## API Contract Summary

### Critical Rules

1. ✅ **ALWAYS include `units` parameter** (consumption & at_a_glance)
2. ✅ **ALWAYS validate meter_uuid is non-empty**
3. ✅ **ALWAYS validate meter_id is non-empty**
4. ✅ **ALWAYS validate days_to_load >= 1**
5. ✅ **ALWAYS check for empty API responses before Pydantic validation**
6. ✅ **Use enums for type safety** (AggregationLevel, RequestUnits)
7. ✅ **Hardcode required fixed values** (source="barnacle", perspective="billing")

### Parameter Cheatsheet

```python
# Consumption API - ALL REQUIRED
{
    "source": "barnacle",                    # Fixed
    "aggregate": aggregation.value,          # Enum (hourly, daily, etc.)
    "units": units.value or "cm",           # Enum with default ⚠️ CRITICAL - always include
    "perspective": "billing",               # Fixed
    "combine": "true",                      # Fixed
    "date": date.strftime("%m/%d/%Y"),      # Formatted datetime
    "display_minutes": True,                # Fixed
    "display_hours": True,                  # Fixed
    "display_days": True,                   # Fixed
    "display_weeks": True,                  # Fixed
    "furthest_zoom": "hr",                  # Fixed
}

# At-a-Glance API
{
    "source": "barnacle",                   # Fixed
    "perspective": "billing",               # Fixed
    "units": units.value or "cm",          # Enum with default (for safety)
}

# Search API
{
    # No params, just query with meter_uuid
}
```
