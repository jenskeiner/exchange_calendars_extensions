---
icon: lucide/tags
---

# Tags

Tags are (short) strings that can be attached to individual days through [calendar changes](changes.md). They are useful
for grouping related days into custom categories.

## Adding tags

Tags are set via the `tags` field of a `DayChange`:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
)

ecx.apply_extensions()

changeset = {
    "2022-12-27": DayChange(tags={"foo", "bar"}),
    "2022-12-28": DayChange(tags={"foo", "foobar"}),
}

ecx.change_calendar("XLON", changeset)

calendar = ec.get_calendar("XLON")

print(calendar.tags(return_tags=True))
```

Output:

```text
2022-12-27       {foo, bar}
2022-12-28    {foo, foobar}
dtype: object
```

Like other holiday calendars, the `tags(...)` method returns a `pandas.DatetimeIndex` when `return_tags=False` (the
default) or a `pandas.Series` when `return_tags=True`.

## Filtering by date range and tags

Use `start`, `end`, and `tags` arguments to filter the results:

```python
import pandas as pd
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
)

ecx.apply_extensions()

changeset = {
    "2022-12-27": DayChange(tags={"foo", "bar"}),
    "2022-12-28": DayChange(tags={"foo", "foobar"}),
}

ecx.change_calendar("XLON", changeset)

calendar = ec.get_calendar("XLON")

print(calendar.tags(start=pd.Timestamp("2022-12-28"), return_tags=True))
print("\n")
print(calendar.tags(end=pd.Timestamp("2022-12-27"), return_tags=True))
print("\n")
print(calendar.tags(tags={"foo"}, return_tags=True))
```

Output:

```text
2022-12-28    {foo, foobar}
dtype: object

2022-12-27    {bar, foo}
dtype: object

2022-12-27       {bar, foo}
2022-12-28    {foo, foobar}
dtype: object
```

!!! note

    When the `tags` argument is provided, a day matches the filter only if *all* given tags are present on that day.
