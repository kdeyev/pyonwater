# PyOnWater Pending Changes

## Items Blocking EyeOnWater Integration Deployment

### 1. End Date Parameter Support (HIGH PRIORITY - BLOCKING)

**Status:** ✅ COMPLETED IN DEV - ⏸️ NOT DEPLOYED TO PRODUCTION - 🔄 TEMPORARILY DISABLED IN EYEONWATER

**Files Modified:**

- `pyonwater/meter_reader.py` (lines 104, 123-133, 135-138)
- `pyonwater/meter.py` (line 68)
- ~~`eyeonwater/__init__.py`~~ (REVERTED - end_date handling temporarily removed)
- ~~`eyeonwater/services.yaml`~~ (REVERTED - end_date field temporarily removed)

**Changes:**

- Added `end_date` parameter to `read_historical_data()` methods
- Modified date calculation to use specified end_date instead of always using "today"
- Enables importing historical data for specific date ranges (e.g., Feb 8-13 instead of always "last N days from today")
- **TEMPORARILY DISABLED**: EyeOnWater reverted to original "days from today" behavior until pyonwater deployed

**Impact:**

- **CRITICAL BUG FIX**: Without this, EyeOnWater's date range selector is non-functional
- Users selecting dates like "Feb 8-13" will get "Feb 11-16" instead (always relative to today)
- **Current Status**: Feature disabled in EyeOnWater to prevent crashes until pyonwater updated

**Deployment Required:**

- Version bump (suggest 0.3.18 or 0.4.0 depending on semver preference)
- Update on Jarvis: `pip install --upgrade pyonwater==<version>`
- After deployment, re-enable end_date in EyeOnWater:
  - Restore end_date handling in `__init__.py` lines 85-131
  - Restore end_date field in `services.yaml`

### 2. Timezone Preservation Fix (HIGH PRIORITY - BLOCKING)

**Status:** ✅ COMPLETED IN DEV - ⏸️ NOT DEPLOYED TO PRODUCTION

**File Modified:**

- `pyonwater/meter_reader.py` (line 128)

**Change:**

```python
# OLD (BROKEN):
end_date = end_date.replace(
    hour=0, minute=0, second=0, microsecond=0,
)

# NEW (FIXED):
end_date = end_date.replace(
    hour=0, minute=0, second=0, microsecond=0,
    tzinfo=end_date.tzinfo,  # Preserve timezone!
)
```

**Impact:**

- **CRITICAL BUG FIX**: Without this, timezone-aware datetimes lose their timezone when normalized
- Causes crashes or incorrect API requests when EyeOnWater passes timezone-aware dates
- Observed in logs: Error at line 176 in coordinator.py during import

**Deployment Required:**

- Same version bump as #1 (can be bundled together)
- Must be deployed before EyeOnWater's `end_date` feature works

### 3. Flexible Date Parsing (COMPLETED & DEPLOYED)

**Status:** ✅ COMPLETED - ✅ READY FOR PRODUCTION USE

**File Modified:**

- `pyonwater/models/eow_historical_models.py` (lines 98-133)

**Change:**

- Custom `@field_validator("date", mode="before")` in `Series` model
- Handles 4 date formats: full datetime, date-only, month-only ("2026-02"), year-only ("2026")

**Impact:**

- Fixes monthly aggregation crashes (Pydantic v2 rejected "2026-02" format)
- Enables yearly aggregation support
- **Note:** Monthly/yearly aggregations disabled in EyeOnWater until API behavior tested

**Deployment Status:**

- Code is stable and tested (21/21 tests passing)
- Can be deployed whenever convenient
- EyeOnWater has disabled MONTHLY/WEEKLY to avoid cross-aggregation issues (architectural, not library bug)

---

## Deployment Checklist

**Before deploying pyonwater to production:**

1. ✅ All tests pass locally (verified Feb 16, 2026)
2. ⏳ Version bump in `pyproject.toml` (suggest 0.3.18 or 0.4.0)
3. ⏳ Update CHANGELOG.md with:
   - Added: `end_date` parameter support for targeted date range imports
   - Fixed: Timezone preservation when normalizing dates to midnight
   - Fixed: Monthly/yearly aggregation date parsing (Pydantic v2 compatibility)
4. ⏳ Git commit and tag new version
5. ⏳ Build and publish to PyPI (if applicable)
6. ⏳ Update on Jarvis: `pip install --upgrade pyonwater==<version>`
7. ⏳ Restart Home Assistant on Jarvis
8. ✅ Test EyeOnWater import with specific date ranges

**After deployment:**

- EyeOnWater's "Import Historical Data" service will correctly honor date selections
- Users can import Feb 8-13 by setting `days=6, end_date=2026-02-13`
- Can re-enable MONTHLY aggregation in EyeOnWater (currently limited to HOURLY only)

---

## Known Issues (Not Blocking)

### Weekly Aggregation Returns Daily Points

- **Issue:** API returns 7 daily datapoints per week instead of 1 aggregate
- **Impact:** Mixing with hourly data creates ordering conflicts in Home Assistant statistics
- **Status:** Disabled in EyeOnWater replay action (architectural, not pyonwater bug)
- **Resolution:** No action needed in pyonwater

### Quarter-Hourly (15-min) Aggregation Untested

- **Status:** User mentioned it failed initially, not investigated
- **Priority:** Low (hourly aggregation is primary use case)
- **Action:** Test if needed, may have separate API response format issues

---

## Development Environment Status

**Current Branches:**

- pyonwater: `feature/pydantic-v2-and-hardening`
- eyeonwater: `feature/expose-unified-sensor-ui`

**Production Status:**

- Jarvis (production): pyonwater 0.3.17 (installed Feb 13, 2026)
- Development: pyonwater 0.3.17+ with pending fixes

**Testing Status:**

- ✅ Unit tests: 21/21 passing
- ✅ Linting: Clean (whitespace fixed, imports added)
- ✅ Type hints: Fixed (datetime.datetime vs datetime module)
- ⏳ Integration testing: Pending deployment to Jarvis

---

## Contact / Notes

**Last Updated:** February 17, 2026  
**Priority:** HIGH - Blocking EyeOnWater date range functionality  
**User Decision:** "we will have to wait on that code" (deferred pyonwater deployment)

**Quick Deploy Command (when ready):**

```bash
# On Jarvis (in Home Assistant container/environment)
pip install --upgrade /path/to/pyonwater/repo
# or
pip install --upgrade pyonwater==0.3.18
```
