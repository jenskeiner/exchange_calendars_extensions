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

## Application modes

`change_calendar()` accepts an optional `mode` argument that controls how the incoming changeset interacts with any
existing changes:

`"merge"` (default)

:   Merges incoming and existing changes per day, following the same [merge rules](changes.md#merge-rules) as
`change_day()`.

`"update"`

:   Updates the existing changeset: an incoming change always overwrites the existing change for the same date.

`"replace"`

:   Replaces the entire existing changeset with the incoming one.

## Clearing all changes

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

For convenience, `remove_changes(exchange)` also clears all changes for a given exchange. Pass `None` to clear
changes for every exchange at once.

## Clearing individual days with CLEAR

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
    ChangeSet,
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

changes: ChangeSet = ecx.get_changes("XLON")

pprint(changes)

print("\n")

ta = TypeAdapter(ChangeSet)
print(ta.dump_json(changes, indent=2).decode())
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
{Timestamp('2022-12-27 00:00:00'): DayChange(type='change', spec=BusinessDaySpec(business_day=True, open=<MISSING>, close=<MISSING>), name=<MISSING>, tags=<MISSING>),
 Timestamp('2022-12-28 00:00:00'): DayChange(type='change', spec=NonBusinessDaySpec(business_day=False, weekend_day=<MISSING>, holiday=True), name='Holiday', tags=<MISSING>)}
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

## Serialisation

Serialising to JSON makes changesets easy to store and transfer.

```python
from pydantic import TypeAdapter
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    ChangeSet,
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

changes: ChangeSet = ecx.get_changes("XLON")

ta = TypeAdapter(ChangeSet)

# Serialize changeset.
serialized = ta.dump_json(changes)

# Deserialize again.
changes_2 = ta.validate_json(serialized)

ecx.change_calendar("XETR", changes_2, mode="replace")

print(ta.dump_json(ecx.get_changes("XETR"), indent=2).decode())
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
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

## Retrieving all changesets

Pass `None` (or omit the argument) to retrieve a dictionary of changesets for every exchange:

```python
from pydantic import TypeAdapter
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    ChangeSet,
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

ecx.change_day("XETR", date="2022-12-30", action=DayChange(spec=BusinessDaySpec()))

changes: dict[str, ChangeSet] = ecx.get_changes()

ta = TypeAdapter(dict[str, ChangeSet])

print(ta.dump_json(changes, indent=2).decode())
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
{
  "XLON": {
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
  },
  "XETR": {
    "2022-12-30 00:00:00": {
      "type": "change",
      "spec": {
        "business_day": true
      }
    }
  }
}
```
