---
icon: lucide/watch
---

# Dates & Times

Working with exchange calendars often requires handling dates and times. This package also uses
[Pydantic](https://github.com/pydantic/pydantic) for convenient validation and serialization, including dates and times.
For convenience, this package defines subclasses of `pandas.Timestamp` and `datetime.time` that can accept flexible
formats work with [Pydantic](https://github.com/pydantic/pydantic)

## `TimestampLike`

This is a subclass of `pandas.Timestamp` that can be safely used in Pydantic models.

```python
import pandas as pd
from exchange_calendars_extensions.datetime import TimestampLike

dt = TimestampLike("2026-04-22")
print(dt)

try:
    TimestampLike(pd.NaT)
except ValueError as e:
    print(e)
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
2026-04-22 00:00:00
Cannot create TimestampLike from NaT or invalid value
```

The only difference to `pandas.Timestamp` is that this type can be used with Pydantic and that the value must be
well-defined, i.e. different from `pandas.NaT`.

## `DateLike`

A direct subclass of `TimestampLike` that normalizes the input to a timezone-naive timestamp at midnight. Date-like
timestamps are often needed when working with exchange calendars.

```python
from exchange_calendars_extensions.datetime import DateLike

dt = DateLike("2026-04-22T05:13:28")
print(dt)
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
2026-04-22 00:00:00
```

## `TimeLike`

Subclasses `dt.time` to accept `HH:MM` and `HH:MM:SS` inputs and can be used with Pydantic.

```python
from exchange_calendars_extensions.datetime import TimeLike

t = TimeLike("15:23:12")
print(t)
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
15:23:12
```

## Usage

This package uses `DateLike` and `TimeLike` extensively in [Pydantic](https://github.com/pydantic/pydantic) models and
the API. For the models, it is important that serialization and deserialization work as expected. In the API, using
these types in combination with [Pydantic](https://github.com/pydantic/pydantic)'s `#!python @validate_call` allows e.g.
to pass dates either as `pandas.Timestamp` or as strings. For example, consider the `#!python change_day()` method.

Using actual class/model instances:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import DayChange, NonBusinessDaySpec
import pandas as pd

ecx.apply_extensions()

ecx.change_day(
    "XLON",
    date=pd.Timestamp("2022-12-28"),
    action=DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
)
```

Using strings and dictionaries:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import DayChange, NonBusinessDaySpec
import pandas as pd

ecx.apply_extensions()

ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=dict(type="change", spec=dict(business_day=False, holiday=True), name="Holiday"),
)
```

See [Calendar Changes](changes.md) for more details on how to change calendars at runtime.
