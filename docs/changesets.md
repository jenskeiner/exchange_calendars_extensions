---
icon: lucide/box
---

# Changesets

Individual day changes can be accumulated in a `ChangeSet` — a dictionary mapping dates to `DayChange` instances. Rather
than modifying days one at a time, you can create and apply an entire changeset to an exchange calendar at once.

## Applying a changeset

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")

assert "2022-12-27" in calendar.holidays_all.holidays()
assert "2022-12-28" not in calendar.holidays_all.holidays()

changeset = {
    "2022-12-27": DayChange(spec=BusinessDaySpec()),
    "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
}

ecx.change_calendar("XLON", changeset)

calendar = ec.get_calendar("XLON")

assert "2022-12-27" not in calendar.holidays_all.holidays()
assert "2022-12-28" in calendar.holidays_all.holidays()
```

## Modes

`change_calendar()` accepts an optional `mode` argument that controls how the incoming changeset interacts with any
existing changes:

`"merge"` (default)

:   Merges incoming and existing changes per day, following the same [merge rules](changes.md#merge-rules) as
`change_day()`.

`"update"`

:   Updates the existing changeset: an incoming change always overwrites the existing change for the same date.

`"replace"`

:   Replaces the entire existing changeset with the incoming one.

## Clearing changes

Pass an empty changeset with `mode="replace"` to remove every change for a calendar:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)

ecx.apply_extensions()

changeset = {
    "2022-12-27": DayChange(spec=BusinessDaySpec()),
    "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
}

ecx.change_calendar("XLON", changeset)

calendar = ec.get_calendar("XLON")

assert "2022-12-27" not in calendar.holidays_all.holidays()
assert "2022-12-28" in calendar.holidays_all.holidays()

ecx.change_calendar("XLON", {}, mode="replace")

calendar = ec.get_calendar("XLON")

assert "2022-12-27" in calendar.holidays_all.holidays()
assert "2022-12-28" not in calendar.holidays_all.holidays()
```

For convenience, `remove_changes(exchange)` also clears all changes for a given exchange.

## Clearing individual days

An incoming changeset can contain `CLEAR` entries to remove the change for specific dates while leaving other dates
untouched:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
    CLEAR,
)

ecx.apply_extensions()

changeset = {
    "2022-12-27": DayChange(spec=BusinessDaySpec()),
    "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
}

ecx.change_calendar("XLON", changeset)

calendar = ec.get_calendar("XLON")

assert "2022-12-27" not in calendar.holidays_all.holidays()
assert "2022-12-28" in calendar.holidays_all.holidays()

changeset_2 = {
    "2022-12-27": CLEAR,
}
ecx.change_calendar("XLON", changeset_2)

calendar = ec.get_calendar("XLON")

assert "2022-12-27" in calendar.holidays_all.holidays()
assert "2022-12-28" in calendar.holidays_all.holidays()
```

## Retrieving changes

Use `get_changes(exchange)` to inspect the current changeset for a calendar:

```python
from pprint import pprint
from pydantic import TypeAdapter
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    ChangeSetDelta,
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)

ecx.apply_extensions()

ecx.change_day("XLON", date="2022-12-27", action=DayChange(spec=BusinessDaySpec()))
ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
)

changes: ChangeSetDelta = ecx.get_changes("XLON")

pprint(changes)

print("\n")

ta = TypeAdapter(ChangeSetDelta)
print(ta.dump_json(changes, indent=2).decode())
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
{
    Timestamp('2022-12-27 00:00:00'): DayChange(
        type='change', spec=BusinessDaySpec(business_day=True, open=<MISSING>, close=<MISSING>),
        name=<MISSING>, tags=<MISSING>),
    Timestamp('2022-12-28 00:00:00'): DayChange(
        type='change', spec=NonBusinessDaySpec(business_day=False, weekend_day=<MISSING>, holiday=True),
        name='Holiday', tags=<MISSING>)
}
```

```json
{
  "2022-12-27 00:00:00": {
    "type": "change",
    "spec": {
      "business_day": true
    }
  },
  "2022-12-28 00:00:00": {
    "type": "change",
    "spec": {
      "business_day": false,
      "holiday": true
    },
    "name": "Holiday"
  }
}
```

!!! note

    As far as typing goes, there is a small but important distinction between a changeset as accepted by
    `change_calendar()` and the internal changeset where changes accumulate as part of a calendar's state.

    The former may also contain `CLEAR` entries to remove specific days from the internal state when applied on
    top of it. The end result, that is, the new state, always only contains `DayChange` entries to describe
    the actual deviations from the vanilla calendar.

    Therefore, `change_calendar()` accepts `ChangeSetDelta` instances while `get_changes()` always returns
    `ChangeSet` instances with the only difference being that the former may contain `CLEAR` entries and
    the latter not.

## Serialization & Deserialization

Serializing to JSON makes changesets easy to store and transfer.

```python
from pydantic import TypeAdapter
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    ChangeSetDelta,
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)

ecx.apply_extensions()

ecx.change_day("XLON", date="2022-12-27", action=DayChange(spec=BusinessDaySpec()))
ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
)

changes: ChangeSetDelta = ecx.get_changes("XLON")

ta = TypeAdapter(ChangeSetDelta)

# Serialize changeset.
serialized = ta.dump_json(changes)

# Deserialize again.
changes_2 = ta.validate_json(serialized)

ecx.change_calendar("XETR", changes_2, mode="replace")

print(ta.dump_json(ecx.get_changes("XETR"), indent=2).decode())
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```json
{
  "2022-12-27 00:00:00": {
    "type": "change",
    "spec": {
      "business_day": true
    }
  },
  "2022-12-28 00:00:00": {
    "type": "change",
    "spec": {
      "business_day": false,
      "holiday": true
    },
    "name": "Holiday"
  }
}
```
