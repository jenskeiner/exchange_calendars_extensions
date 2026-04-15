# exchange-calendars-extensions

[![PyPI](https://img.shields.io/pypi/v/exchange-calendars-extensions)](https://pypi.org/project/exchange-calendars-extensions/) ![Python Support](https://img.shields.io/pypi/pyversions/exchange_calendars_extensions) ![PyPI Downloads](https://img.shields.io/pypi/dd/exchange-calendars-extensions)

A Python package that transparently adds some features to
the [exchange-calendars](https://pypi.org/project/exchange-calendars/)
package.

For all exchanges:

- Calendars that aggregate existing regular and ad-hoc holidays/special open days/special close days, respectively, into
  a single calendar.
- Calendars for the last trading session of each month, and the last *regular* trading session of each month.
- Calendars for weekend and week days.
- The ability to modify the properties of days at runtime.
- The ability to attach and query arbitrary tags to days.

For select exchanges:

- Calendars for additional special trading sessions, such as monthly and quarterly expiry days (aka quadruple witching).

## Aggregate calendars

These additional calendars aggregate regular and ad-hoc holidays/special open/special close days, respectively, into a
single calendar. This can be convenient to avoid having to querying multiply calendars on the original exchange
calendar.

*Note: Aggregate calendars for special open/close days may combine days with different session times. From the aggregate
calendar alone, the open/close time cannot be recovered.*

## Additional calendars

In addition to information that is already available in
[exchange-calendars](https://pypi.org/project/exchange-calendars/), this package also adds calendars for

- the last trading session of each month,
- the last *regular* trading session of each month, and
- weekend and week days, as per the underlying weekmask.

For select exchanges (see [below](#supported-exchanges-for-monthlyquarterly-expiry)), this package also adds calendars
for:

- quarterly expiry days (aka quadruple witching), and
- monthly expiry days (in all remaining months that don't have a quarterly expiry day).

## Calendar modifications and tags

Ideally, exchange calendars from [exchange-calendars](https://pypi.org/project/exchange-calendars/) always provide a
correct view. In reality though, exchanges
sometimes adjust their trading schedule, in some instances even on short notice. This poses a challenge as the typical
release cycles implies that necessary adjustments to adapt the calendars to reality may not be possible in a timely
manner.

To address this issue, this package adds the ability to modify exchange calendars at runtime. This can generally convert
any day into a business or non-business day with the desired properties. In addition, arbitrary tags can be attached to
days, e.g. to group days into custom categories.

## Installation

The package is available on [PyPI](https://pypi.org/project/exchange-calendars-extensions/) and can be installed via
[pip](https://pip.pypa.io/en/stable/) or any other suitable package/dependency management tool, e.g.
[Poetry](https://python-poetry.org/).

```bash
pip install exchange-calendars-extensions
```

## General usage

*Note: In general, any code snippet in this documentation is self-contained and should execute successfully in a fresh
Python interpreter instance*

Import `exchange_calendars_extensions.core` and register extended exchange calendar classes with the
`exchange_calendars` module.

```python
import exchange_calendars_extensions.core as ecx

ecx.apply_extensions()
```

This replaces the default exchange calendar classes with their extended versions.

Get an exchange calendar instance and verify that extended exchange calendars are subclasses of the abstract base
class `ecx.ExtendedExchangeCalendar`. This class inherits both from `ec.ExchangeCalendar` and the new protocol class
`ecx.ExchangeCalendarExtensions` which defines the extended properties.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")

# It's still a regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# But it's also an extended exchange calendar...
assert isinstance(calendar, ecx.ExtendedExchangeCalendar)
# ...and implements the extended protocol.
assert isinstance(calendar, ecx.ExchangeCalendarExtensions)
```

The original classes can be re-instated by calling `ecx.remove_extensions()`.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx

ecx.apply_extensions()

...

ecx.remove_extensions()

calendar = ec.get_calendar("XLON")

# It's a regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# But it's not an extended exchange calendar anymore.
assert not isinstance(calendar, ecx.ExtendedExchangeCalendar)
assert not isinstance(calendar, ecx.ExchangeCalendarExtensions)
```

## Additional properties

Extended exchange calendars have additional properties:

| Property                         | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `holidays_all`                   | Regular and ad-hoc holidays in single calendar.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `special_opens_all`              | Regular and ad-hoc special open days in a single calendar.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `special_closes_all`             | Regular and ad-hoc special close days in a single calendar.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `weekend_days`                   | Weekend days, as defined by the underlying weekmask, in a single calendar.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `week_days`                      | Week days (the complement of weekend days) in a single calendar.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `quarterly_expiries`             | Quarterly expiry days, also known as quadruple witching.<br><br> Many exchanges observe special business days on which market index futures, options futures, stock options and stock futures expire, typically resulting in increased volatility and traded volume. Quadruple witching is typically observed on the third Friday of March, June, September and December, although some exchanges observe it on Thursday instead. Note that in the case of collisions with holidays or special open/close days, a quarterly expiry day is usually rolled backward to the previous regular business day. |
| `monthly_expiries`               | Monthly expiry days. Similar to quarterly expiry days, but for all remaining months of the year. Provided in a separate calendar as they typically result in less extreme trading patterns.                                                                                                                                                                                                                                                                                                                                                                                                             |
| `last_session_of_months`         | Calendar with the last trading session for each month of the year.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `last_regular_session_of_months` | Calendar with the last regular trading session of each month of the year, i.e. not a special open/close or otherwise irregular day.                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `last_regular_session_of_months` | Calendar with the last regular trading session of each month of the year, i.e. not a special open/close or otherwise irregular day.                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `tags`                           | Method to query day ranges for given tags.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

For example,

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")
print(
    calendar.holidays_all.holidays(
        start="2020-01-01", end="2020-12-31", return_name=True
    )
)
```

will output

```text
2020-01-01         New Year's Day
2020-04-10            Good Friday
2020-04-13          Easter Monday
2020-05-08                    NaN
2020-05-25    Spring Bank Holiday
2020-08-31    Summer Bank Holiday
2020-12-25              Christmas
2020-12-26             Boxing Day
2020-12-28     Weekend Boxing Day
dtype: object
```

Note: NumPy's `NaN` indicates holidays without a specific name in
[exchange-calendars](https://pypi.org/project/exchange-calendars/)'s model, e.g. ad-hoc holidays such as 2020-05-08
(May Day bank holiday was moved in honor of the 75th VE Day anniversary).

Quarterly and monthly expiry days:

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")
print(calendar.quarterly_expiries.holidays(start="2023-01-01", end="2023-12-31"))
print(calendar.monthly_expiries.holidays(start="2023-01-01", end="2023-12-31"))
```

will output

```text
DatetimeIndex(['2023-03-17', '2023-06-16', '2023-09-15', '2023-12-15'], dtype='datetime64[us]', freq=None)
DatetimeIndex(['2023-01-20', '2023-02-17', '2023-04-21', '2023-05-19',
               '2023-07-21', '2023-08-18', '2023-10-20', '2023-11-17'],
              dtype='datetime64[us]', freq=None)
```

Note: Expiry day calendars do not provide names so using `return_name=True` only makes sens if you definitely need a
Pandas `Series` and not a `DatetimeIndex`.

Last trading days of months:

Similar to the expiry day calendars, the last (regular) trading day of a month calendars do not provide names.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")
print(
    calendar.last_trading_days_of_months.holidays(start="2023-01-01", end="2023-12-31")
)
print(
    calendar.last_regular_trading_days_of_months.holidays(
        start="2023-01-01", end="2023-12-31"
    )
)
```

will output

```text
DatetimeIndex(['2023-01-31', '2023-02-28', '2023-03-31', '2023-04-28',
               '2023-05-31', '2023-06-30', '2023-07-31', '2023-08-31',
               '2023-09-29', '2023-10-31', '2023-11-30', '2023-12-29'],
              dtype='datetime64[us]', freq=None)
DatetimeIndex(['2023-01-31', '2023-02-28', '2023-03-31', '2023-04-28',
               '2023-05-31', '2023-06-30', '2023-07-31', '2023-08-31',
               '2023-09-29', '2023-10-31', '2023-11-30', '2023-12-28'],
              dtype='datetime64[us]', freq=None)
```

Notice the difference in December where 2023-12-29 is a special close day, so 2023-12-28 is the last regular trading day
in that month for XLON.

## Calendar Changes

Extended exchange calendars not only provide additional properties, they can also be adjusted at runtime. This allows
you, for example, to convert a regular business day into a special open/close day or a holiday, or to convert a weekend
day into a regular trading day.

### The Model

Before looking at how changes are effected, it is important to consider the model used to represent changes. To that
end, let's consider a single day `d` in an exchange calendar. Of course, `d` has certain properties in the yet unchanged
exchange calendar. It may be a regular business day, a holiday, or something else. This is the pristine state of `d`.

A change to `d` describes a layer that can be put on top of `d`'s current state to change some or all of its properties.
It is described by the `DayChange` [Pydantic](https://github.com/pydantic/pydantic) model and sub-models:

```python
from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING
from exchange_calendars_extensions.core import DaySpec


class DayChange(BaseModel):
    spec: DaySpec | None | MISSING = MISSING
    name: str | None | MISSING = MISSING
    tags: set[str] | MISSING = MISSING
```

Notice that this uses the experimental `MISSING` sentinel introduced in [Pydantic](https://github.com/pydantic/pydantic)
2.12.0 which indicates undefined fields. This is useful instead of using `None` as a sentinel since `None`may have a
well-defined meaning other than an undefined value for certain fields. For a `DayChange`, a field with a value of
`MISSING` means
that the field is unspecified in the change and so the corresponding underlying properties of the day are left
unchanged. This way, a `DayChange` can represent a delta or a partial layer to apply on top of the current state of a
day.

The fields have the following meaning:

| Property | Description                                          |
|----------|------------------------------------------------------|
| `spec`   | Core properties of the business or non-business day. |
| `name`   | The name of the day.                                 |
| `tags`   | A set of tags.                                       |

The `name` property can be used to assign a name to a day, but note that this will only be visible if the day is a
regular holiday or regular special open/close day.

### DaySpec

The `spec` property describes the core properties of the day, depending on whether it is a business day or a
non-business day. The corresponding `DaySpec` type is a discriminated union of `BusinessDaySpec` and
`NonBusinessDaySpec`.

```python
from typing import Annotated
from pydantic import Field
from exchange_calendars_extensions.core import NonBusinessDaySpec, BusinessDaySpec

DaySpec = Annotated[
    NonBusinessDaySpec | BusinessDaySpec, Field(discriminator="business_day")
]
```

A non-business day, is described by `NonBusinessDaySpec`.

```python
from typing import Literal
from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING


class NonBusinessDaySpec(BaseModel):
    business_day: Literal[False] = False
    weekend_day: bool | MISSING = MISSING
    holiday: bool | MISSING = MISSING
```

It can be either a weekend day or a holiday, or both. Note that validation ensures that at least one of `weekend_day`
or `holiday` is `True`.

A business day is described by `BusinessDaySpec`.

```python
from typing import Literal
from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING
from exchange_calendars_extensions.core.datetime import TimeLike


class BusinessDaySpec(BaseModel):
    business_day: Literal[True] = True
    open: TimeLike | Literal["regular"] | MISSING = MISSING
    close: TimeLike | Literal["regular"] | MISSING = MISSING
```

A business day must have a trading session with a defined open and close time. The times can be specified explicitly or
implicitly as a reference to the regular open/close time (`regular`). A `MISSING` value uses the open/close time of the
underlying unmodified day, if it is a business day, or the regular open/close time, otherwise.

Here, `TimeLike` is a `datetime.time` subtype that can be used with Pydantic and supports initialization from strings
in `HH:MM` or `HH:MM:SS` format for convenience.

### Tags

Tags are sets of typically short strings that can be used to group related days.

### Examples

The `DayChange` model can express a wide range of complete or partial changes to a day. For example, the following
change only sets the name of a day, but leaves everything else unchanged

```python
from exchange_calendars_extensions.core import DayChange

DayChange(name="Holiday")
```

Such change applied to a day that is either a regular holiday or regular special open/close day will only alter its
name. But note that application to a regular business day will not have any effect as only calendars for regular special
days support names on days.

The following change describes a special open day:

```python
from exchange_calendars_extensions.core import DayChange, BusinessDaySpec
import datetime as dt

DayChange(
    spec=BusinessDaySpec(open=dt.time(11, 0), close="regular"), name="Special Open"
)
```

It can be applied to any business or non-business day to convert it into a special open day. The optional `name` can be
left undefined here to retain the existing name (or `None`) of the day.

Likewise, the following change describes a weekend day that is also a holiday, and assigns some tags as well

```python
from exchange_calendars_extensions.core import DayChange, NonBusinessDaySpec

DayChange(
    spec=NonBusinessDaySpec(weekend_day=True, holiday=True),
    name="Weekend Holiday",
    tags={"foo", "bar"},
)
```

## Applying calendar changes

To apply a change to a single day, use the `change_day(...)` method.

For example, to add a new holiday:

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import DayChange, NonBusinessDaySpec
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

### Stacked changes to a single day

A change to a day becomes part of the calendar's state. You can apply a second change to the same day to adjust the
properties again. By default, the second change will be applied on top of the first change.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import DayChange, NonBusinessDaySpec
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

When a second change `incoming` gets applied on top of an existing change `current`, both changes are merged. Generally,
if a property is specified only in `actual` or in `incoming`, but not the other, it is retained in the result, and if
both changes do not specify it, then so does the result. However, if the property is specified in both changes, they are
merged as follows:

| Property               | Merging Behavior                                                                       |
|------------------------|----------------------------------------------------------------------------------------|
| spec (same type)       | Merge the specs on their properties, where conflicting, use the value from `incoming`. |
| spec (different types) | Use the spec from `incoming`.                                                          |
| name                   | Use the name from `incoming`                                                           |
| tags                   | Use the set union of tags from `actual`and `incoming`.                                 |                                                                                                                                                          |

See the following example:

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

### Reverting changes

To remove any changes to a day and recover the original state, use `change_day(...)` with the `CLEAR` sentinel:

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

It is not possible to revert select fields of an already applied change back to an undefined state through another
change. For example, you cannot first change the name of a day with one change, and then clear the name field through a
second change applied on top. The only way is to reset the day and then apply the desired change.

### Specifying dates, times, and day types

Thanks to Pydantic's runtime validation, most functions accept dates, times, day changes, et cetera in different formats
and parse them automatically into the correct type.

For dates, you may use `pandas.Timestamp`, `datetime.date`, or simply a strings in ISO format `YYYY-MM-DD`.

For times, you can use `datetime.time`, strings in the format `HH:MM:SS` or `HH:MM`. To specify a session open or close
time for a day modification, you can also use the sentinel `'regular'` to refer to the prevailing standard time.

### Visibility of Changes

Whenever a calendar is modified, the changes are only reflected after obtaining a new instance.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

## Changesets

So far, we have considered only changes to a single day which become part of the affected calendar's state. This state
is captured in a `ChangeSet` which is just a dictionary mapping dates to changes.

To make working with multiple changes easier, it is possible to create and apply entire changesets at once.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

The function `change_calendar()` supports an optional argument `mode` which can be set to `"replace"`, `"update"`, or
`"merge"` to control how the changes are applied.

- The default is `"merge"`, which merges existing and new changes on a per-day basis, just how `change_day()` works.
- When set to `"update"`, the existing changeset is just updated with the new changes, so an incoming change always
- overwrites an existing change.
- When set to `"replace"`, the existing changeset is replaced entirely with the new changes.
-

The `change_calendar` function can also be used to clear all changes to a calendar:

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

For convenience, the function `remove_changes(exchange: str | None)` also clears all changes for a given exchange, or
for all exchanges if `exchange` is `None`.

An incoming changeset may contain `CLEAR` entries to remove changes for specific dates.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

### Retrieving the Changeset for a Calendar

You can inspect the current state of a calendar directly to verify what changes have been applied using
`get_changes(exchange: str | None)`.

```python
from pprint import pprint
from pydantic import TypeAdapter
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

This will output

```
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

Serializing to JSON makes changes easy to store and pass around.

```python
from pydantic import TypeAdapter
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

serialized = ta.dump_json(changes)

changes_2 = ta.validate_json(serialized)

ecx.change_calendar("XETR", changes_2, mode="replace")

print(ta.dump_json(ecx.get_changes("XETR"), indent=2).decode())
```

Set `exchange` to `None` to retrieve a dictionary of all changesets for all exchanges.

```python
from pydantic import TypeAdapter
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

This prints

```
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

## Tags

Custom tags can be added through calendar changes as well.

```python
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

This will output

```
2022-12-27       {foo, bar}
2022-12-28    {foo, foobar}
dtype: object
```

Like other holiday calendars, this function either returns a `pandas.DatetimeIndex` when `return_tags=False` (the
default) or a `pandas.Series` when `return_tags=True`.

Likewise, dates can be filtered via `start` and `end` arguments, as well as a set of required tags.

```python
import pandas as pd
import exchange_calendars as ec
import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core.changes import (
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

The result:

```
2022-12-28    {foo, foobar}
dtype: object

2022-12-27    {bar, foo}
dtype: object

2022-12-27       {bar, foo}
2022-12-28    {foo, foobar}
dtype: object
```

When the `tags` argument is given, all provided tags must be present on a day to match the filter.

## Supported exchanges for monthly/quarterly expiry

This package currently provides support for monthly/quarterly expiry calendars for the following subset of exchanges
from `exchange_calendars`:

- ASEX
- BMEX
- XAMS
- XBRU
- XBUD
- XCSE
- XDUB
- XETR
- XHEL
- XIST
- XJSE
- XLIS
- XLON
- XMAD
- XMIL
- XNAS
- XNYS
- XOSL
- XPAR
- XPRA
- XSTO
- XSWX
- XTAE
- XTSE
- XWAR
- XWBO

## Advanced usage

### Adding an extended calendar for a new exchange

To facilitate the creation of extended exchange calendar classes, the function `extend_class` is provided in the
submodule `exchange_calendars_extensions.holiday_calendar`.

```python
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars_extensions.core import extend_class

xlon_extended_cls = extend_class(XLONExchangeCalendar, day_of_week_expiry=4)
```

The first argument to `extend_class` should be the class of the exchange calendar to extend. The second and optional
parameter, which defaults to `None`, is the day of the week on which expiry days are normally observed. If this
parameter
is `None`, this assumes that the underlying exchange does not support monthly or quarterly expiry days and the
respective
calendars will not be added.

The returned extended class directly inherits from the passed base class and adds the additional attributes like
`holidays_all` et cetera. The returned class also supports programmatic modifications using the corresponding exchange
key of the parent class.

To register a new extended class for an exchange, use the `register_extension()` function before calling
`apply_extensions()`.

```python
from exchange_calendars_extensions.core import register_extension, apply_extensions

register_extension("XLON", day_of_week_expiry=4)
apply_extensions()
...
```

Here, `key` should be the name, i.e. not an alias, under which the extended class is registered with the
`exchange_calendars` package, and `cls` should be the extended class.

## Caveat: Merging holiday calendars

For the various calendars, [exchange-calendars](https://pypi.org/project/exchange-calendars/) defines and uses the class
`exchange_calendars.exchange_calendar.HolidayCalendar` which is a direct subclass of the abstract base class
`pandas.tseries.holiday.AbstractHolidayCalendar`.

One of the assumptions of `AbstractHolidayCalendar` is that each contained rule that defines a holiday has a unique
name. Thus, when merging two calendars via the `.merge()` method, the resulting calendar will only retain a single rule
for each name, eliminating any duplicates.

This creates a problem with the calendars provided by this package. For example, constructing the holiday calendar
backing `holidays_all` requires to add a rule for each ad-hoc holiday. However, since ad-hoc holidays don't define a
unique name, each rule would either have to generate a unique name for itself, or use the same name as the other rules.
This package uses the latter approach, i.e. all ad-hoc holidays are assigned the same name `ad-hoc holiday`.

As a result, the built-in merge functionality of `AbstractHolidayCalendar` would eliminate all but one of the ad-hoc
holidays when merging with another calendar. This is not the desired behavior.

To avoid this problem, this package defines the function `merge_calendars(calendars: Iterable[AbstractHolidayCalendar])`
which returns a calendar that simply concatenates, in order, all rules from the passed-in calendars. The returned
calendar is a subclass of `HolidayCalendar` that handles possible duplicates by filtering them out before returning
from a call to `holidays()`.

**In essence: Always use `merge_calendars(...)` instead of `AbstractHolidayCalendar.merge(...)` when merging involves
any of the calendars added by this package. Keep in mind that for duplicate elimination, rules more to the front of the
list have higher priority.**

## Contributing

Contributions are welcome. Please open an issue or submit a pull request on GitHub.
