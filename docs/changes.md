---
icon: lucide/square-pen
---

# Calendar changes

Extended exchange calendars can be modified at runtime. This can convert any day into a business day or
non-business day with the desired properties — useful when an exchange adjusts its trading schedule on short notice.

## The change model

A change to a day is described by the `DayChange` [Pydantic](https://github.com/pydantic/pydantic) model:

```python
from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING
from exchange_calendars_extensions import DaySpec


class DayChange(BaseModel):
    spec: DaySpec | None | MISSING = MISSING
    name: str | None | MISSING = MISSING
    tags: set[str] | MISSING = MISSING
```

The fields are:

`spec`

:   Core properties of the business or non-business day.

`name`

:   The name of the day; visible when the day is a regular holiday or regular special open/close day.

`tags`

:   A set of tags; see [Tags](tags.md).

!!! note

    A field set to `MISSING` (the experimental Pydantic sentinel introduced in 2.12.0) means "leave the underlying
    property unchanged". This allows a `DayChange` to act as a partial delta on top of a day's current state.

### DaySpec

The `spec` field is
a [discriminated union](https://pydantic.dev/docs/validation/latest/concepts/unions/#discriminated-unions) of
`BusinessDaySpec` and `NonBusinessDaySpec`.

```python
from typing import Annotated
from pydantic import Field
from exchange_calendars_extensions import NonBusinessDaySpec, BusinessDaySpec

DaySpec = Annotated[
    NonBusinessDaySpec | BusinessDaySpec, Field(discriminator="business_day")
]
```

#### NonBusinessDaySpec

Represents properties of a non-business day.

```python
from typing import Literal
from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING


class NonBusinessDaySpec(BaseModel):
    business_day: Literal[False] = False
    weekend_day: bool | MISSING = MISSING
    holiday: bool | MISSING = MISSING
```

A non-business day can be a weekend day, a holiday, or both. Validation ensures at least one of `weekend_day` or
`holiday` is `True`.

!!! note

    A day that turns into a holiday always becomes a *regular* holiday, with an optional name, never an *ad-hoc
    holiday*.

#### BusinessDaySpec

Represents properties of a business day.

```python
from typing import Literal
from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING
from exchange_calendars_extensions.datetime import TimeLike


class BusinessDaySpec(BaseModel):
    business_day: Literal[True] = True
    open: TimeLike | Literal["regular"] | MISSING = MISSING
    close: TimeLike | Literal["regular"] | MISSING = MISSING
```

A business day has a trading session with a defined open and close time. These can be:

- An explicit time — `TimeLike` is a subclass of `datetime.time` that also accepts strings in `HH:MM` or `HH:MM:SS`
  format.
- The literal `"regular"` — refers to the exchange's prevailing standard open/close time at the respective date.
- `MISSING` — uses the open/close time of the underlying unmodified day, if it is already a business day, or the
  regular time otherwise.

!!! note

    A day that turns into a special open or close day, or both, always becomes a *regular* special open/close day, with
    an optional name, never an *ad-hoc special open/close day*.

## Name

In the model of [exchange-calendars](https://pypi.org/project/exchange-calendars/), only regular holidays or regular
special open/close days can have names.
However, if a day is a special open *and* a special close day, it could in theory even have two different names.

For calendar changes, you can assign, clear (`None`), or inherit (`MISSING`) a single name for a day, regardless of
whether it's a business day or not. Importantly, if a name is assigned, it can only become visible if the day is a
regular holiday or a regular special open/close day after the changes. Otherwise, any assigned name will not be visible.

!!! note

    If a day becomes a special open *and* a special close day at the same time and a name is assigned, then that single
    name is used. If a name is inherited and the day was a special open *and* a special close day at the same time, then
    the particular choice of the name to inherit (from special open or close) is undefined.

## Examples

**Set only the name** (leaves everything else unchanged):

```python
from exchange_calendars_extensions import DayChange

DayChange(name="Holiday")
```

**Create a special open day:**

```python
from exchange_calendars_extensions import DayChange, BusinessDaySpec
import datetime as dt

DayChange(
    spec=BusinessDaySpec(open=dt.time(11, 0), close="regular"), name="Special Open"
)
```

**Create a weekend day that is also a holiday, with tags:**

```python
from exchange_calendars_extensions import DayChange, NonBusinessDaySpec

DayChange(
    spec=NonBusinessDaySpec(weekend_day=True, holiday=True),
    name="Weekend Holiday",
    tags={"foo", "bar"},
)
```

## Applying a change

Use `change_day(...)` to apply a change to a single day.

```python hl_lines="18 19 20 21 22"
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import DayChange, NonBusinessDaySpec
import pandas as pd

ecx.apply_extensions()

d = pd.Timestamp("2022-12-28")

calendar = ec.get_calendar("XLON")

assert d not in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d not in calendar.holidays_all.holidays()
assert d not in calendar.weekend_days.holidays()
assert calendar.day.rollforward(d) == d

ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
)

calendar = ec.get_calendar("XLON")

assert d in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d in calendar.holidays_all.holidays()
assert d not in calendar.weekend_days.holidays()  # It's not a weekend day.
assert (
        calendar.regular_holidays.holidays(start=d, end=d, return_name=True)[d] == "Holiday"
)
assert calendar.day.rollforward(d) == pd.Timestamp("2022-12-29")
```

## Stacking changes

Once a change is applied to a day, it becomes part of the exchange calendar's state. A second call to `change_day(...)`
for the same day merges the incoming change on top of the existing one:

```python hl_lines="10 11 12 13 14 27 28 29 30 31"
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import DayChange, NonBusinessDaySpec
import pandas as pd

ecx.apply_extensions()

d = pd.Timestamp("2022-12-28")

ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
)

calendar = ec.get_calendar("XLON")

assert d in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d in calendar.holidays_all.holidays()
assert d not in calendar.weekend_days.holidays()
assert (
        calendar.regular_holidays.holidays(start=d, end=d, return_name=True)[d] == "Holiday"
)
assert calendar.day.rollforward(d) == pd.Timestamp("2022-12-29")

ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(weekend_day=True), name="Changed again"),
)

calendar = ec.get_calendar("XLON")

assert d in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d in calendar.holidays_all.holidays()
assert d in calendar.weekend_days.holidays()  # It's now a weekend day, too.
assert (
        calendar.regular_holidays.holidays(start=d, end=d, return_name=True)[d]
        == "Changed again"
)
assert calendar.day.rollforward(d) == pd.Timestamp("2022-12-29")
```

### Merge rules

The different fields of a change behave differently under merging conditions. Merging occurs, if a fields is present in
the existing change, as well as the change that applies on top. The fields are merged as follows:

`spec` (same type)

:   Merge property-by-property; for conflicting values, use the incoming change.

`spec` (different type)

:   Use the incoming spec.

`name`

:    Use the incoming name.

`tags`

:   Take the set union of both tag sets.

Example:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    BusinessDaySpec,
    NonBusinessDaySpec,
)
import pandas as pd

ecx.apply_extensions()

d = pd.Timestamp("2022-12-28")

ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
)

ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(weekend_day=True), name="Changed again"),
)

calendar = ec.get_calendar("XLON")

assert d in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d in calendar.holidays_all.holidays()
assert d in calendar.weekend_days.holidays()  # It's now a weekend day, too.
assert d not in calendar.week_days.holidays()
assert (
        calendar.regular_holidays.holidays(start=d, end=d, return_name=True)[d]
        == "Changed again"
)
assert calendar.day.rollforward(d) == pd.Timestamp("2022-12-29")

ecx.change_day("XLON", date="2022-12-28", action=DayChange(spec=BusinessDaySpec()))

calendar = ec.get_calendar("XLON")

assert d not in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d not in calendar.holidays_all.holidays()
assert d not in calendar.weekend_days.holidays()
assert d in calendar.week_days.holidays()  # It's a regular business day, again.
assert calendar.day.rollforward(d) == d
```

## Reverting changes

Use `change_day(...)` with the `CLEAR` sentinel to remove all changes for a day and recover the original state:

```python hl_lines="34"
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    NonBusinessDaySpec,
    CLEAR,
)
import pandas as pd

ecx.apply_extensions()

d = pd.Timestamp("2022-12-28")

ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(
        spec=NonBusinessDaySpec(holiday=True, weekend_day=True), name="Holiday"
    ),
)

calendar = ec.get_calendar("XLON")

assert d in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d in calendar.holidays_all.holidays()
assert d in calendar.weekend_days.holidays()
assert d not in calendar.week_days.holidays()
assert (
        calendar.regular_holidays.holidays(start=d, end=d, return_name=True)[d] == "Holiday"
)
assert calendar.day.rollforward(d) == pd.Timestamp("2022-12-29")

ecx.change_day("XLON", date="2022-12-28", action=CLEAR)

calendar = ec.get_calendar("XLON")

assert d not in calendar.regular_holidays.holidays()
assert d not in calendar.adhoc_holidays
assert d not in calendar.holidays_all.holidays()
assert d not in calendar.weekend_days.holidays()
assert d in calendar.week_days.holidays()
assert calendar.day.rollforward(d) == d
```

!!! warning

    It is currently not possible to revert individual fields of an already applied change to an undefined state through
    another change. To achieve that, clear the day with `CLEAR` and then re-apply the desired change from scratch.

## Visibility of changes

Changes are only reflected after obtaining a *new* calendar instance:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars_extensions.changes import (
    DayChange,
    NonBusinessDaySpec,
    BusinessDaySpec,
)

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")

# Unchanged calendar.
assert "2022-12-27" in calendar.holidays_all.holidays()
assert "2022-12-28" not in calendar.holidays_all.holidays()

# Modify calendar. This clears the cache, so ec.get_calendar('XLON') will return a new instance next time.
ecx.change_day(
    "XLON",
    date="2022-12-27",
    action=DayChange(spec=BusinessDaySpec(open="regular", close="regular")),
)
ecx.change_day(
    "XLON",
    date="2022-12-28",
    action=DayChange(spec=NonBusinessDaySpec(holiday=True), name="Holiday"),
)

# Changes not reflected in existing instance.
assert "2022-12-27" in calendar.holidays_all.holidays()
assert "2022-12-28" not in calendar.holidays_all.holidays()

# Get new instance.
calendar = ec.get_calendar("XLON")

# Changes reflected in new instance.
assert "2022-12-27" not in calendar.holidays_all.holidays()
assert "2022-12-28" in calendar.holidays_all.holidays()

# Revert the changes.
ecx.remove_changes("XLON")

# Get new instance.
calendar = ec.get_calendar("XLON")

# Changes reverted in new instance.
assert "2022-12-27" in calendar.holidays_all.holidays()
assert "2022-12-28" not in calendar.holidays_all.holidays()
```
