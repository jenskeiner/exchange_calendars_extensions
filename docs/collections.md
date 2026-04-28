---
icon: lucide/boxes
---

# Multiple changesets

On top of changes to single days and single calendars, it is also possible to apply changes to an entire set of
calendars in bulk via a `#!python ChangeSetDeltaDict = dict[str, ChangeSetDelta]`.

## Applying multiple changesets

Use `change_calendars()` to apply multiple changesets at once.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)

ecx.apply_extensions()

calendar_xlon = ec.get_calendar("XLON")
calendar_xetr = ec.get_calendar("XETR")

assert "2022-12-27" in calendar_xlon.holidays_all.holidays()
assert "2022-12-28" not in calendar_xlon.holidays_all.holidays()
assert "2022-12-17" in calendar_xetr.weekend_days.holidays()

changeset_dict = {
    "XLON": {
        "2022-12-27": DayChange(spec=BusinessDaySpec()),
        "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
    },
    "XETR": {
        "2022-12-17": DayChange(spec=BusinessDaySpec()),
    }
}

ecx.change_calendars(changeset_dict)

calendar_xlon = ec.get_calendar("XLON")
calendar_xetr = ec.get_calendar("XETR")

assert "2022-12-27" not in calendar_xlon.holidays_all.holidays()
assert "2022-12-28" in calendar_xlon.holidays_all.holidays()
assert "2022-12-17" not in calendar_xetr.weekend_days.holidays()
```

## Modes

`change_calendars()` also accepts an optional `mode` argument. The modes `merge`, `update` and `replace` work the same
as for `change_calendar()` and apply at the calendar level. Additionally, the mode`replace_all` clears out all existing
changesets for all calendars before applying the new ones.

```python
import pandas as pd
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)

ecx.apply_extensions()

changeset_dict = {
    "XLON": {
        "2022-12-27": DayChange(spec=BusinessDaySpec()),
        "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
    },
    "XETR": {
        "2022-12-17": DayChange(spec=BusinessDaySpec()),
    }
}

ecx.change_calendars(changeset_dict)

changeset_dict_2 = {
    "XWBO": {
        pd.Timestamp("2022-12-17"): DayChange(spec=BusinessDaySpec()),
    }
}

ecx.change_calendars(changeset_dict_2, mode="replace_all")

assert ecx.get_changes() == changeset_dict_2
```

## Clearing changes

Similar to `change_calendar()`, pass an empty dictionary and `mode="replace_all"` to remove all changesets for all
calendars.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)

ecx.apply_extensions()

changeset_dict = {
    "XLON": {
        "2022-12-27": DayChange(spec=BusinessDaySpec()),
        "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
    },
    "XETR": {
        "2022-12-17": DayChange(spec=BusinessDaySpec()),
    }
}

ecx.change_calendars(changeset_dict)

ecx.change_calendars({}, mode="replace_all")

assert ecx.get_changes() == {}
```

For convenience, `remove_changes()`, called without any argument, also clears all changesets to the same effect.

## Retrieving changes

Use `get_changes()` (without any argument) to retrieve the changesets for all exchanges.

```python
from pydantic import TypeAdapter
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
    ChangeSetDict
)

ecx.apply_extensions()

changeset_dict = {
    "XLON": {
        "2022-12-27": DayChange(spec=BusinessDaySpec()),
        "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
    },
    "XETR": {
        "2022-12-17": DayChange(spec=BusinessDaySpec()),
    }
}

ecx.change_calendars(changeset_dict)

changes: ChangeSetDict = ecx.get_changes()

ta = TypeAdapter(ChangeSetDict)

print(ta.dump_json(changes, indent=2).decode())
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```json
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
    "2022-12-17 00:00:00": {
      "type": "change",
      "spec": {
        "business_day": true
      }
    }
  }
}
```

## Serialization & Deserialization

As with individual changesets, serialization and deserialization work via Pydantic.

```python
from pydantic import TypeAdapter
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
    ChangeSetDeltaDict
)

ecx.apply_extensions()

changeset_dict = {
    "XLON": {
        "2022-12-27": DayChange(spec=BusinessDaySpec()),
        "2022-12-28": DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
    },
    "XETR": {
        "2022-12-17": DayChange(spec=BusinessDaySpec()),
    }
}

ta = TypeAdapter(ChangeSetDeltaDict)

# Serialize changeset.
serialized = ta.dump_json(changeset_dict)

# Deserialize again.
changeset_dict_2 = ta.validate_json(serialized)

ecx.change_calendars(changeset_dict_2, mode="replace_all")

print(ta.dump_json(ecx.get_changes(), indent=2).decode())
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```json
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
    "2022-12-17 00:00:00": {
      "type": "change",
      "spec": {
        "business_day": true
      }
    }
  }
}
```
