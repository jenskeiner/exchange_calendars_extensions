---
icon: lucide/calendar-plus
---

# Additional properties

Extended exchange calendars expose additional properties beyond those available in
[exchange-calendars](https://pypi.org/project/exchange-calendars/).

## Property reference

`holidays_all`

:   Regular and ad-hoc holidays in a single calendar.

`special_opens_all`

:   Regular and ad-hoc special open days in a single calendar.

`special_closes_all`

:   Regular and ad-hoc special close days in a single calendar.

`weekend_days`

:   Weekend days, as defined by the underlying weekmask, in a single calendar.

`week_days`

:   Week days (the complement of weekend days) in a single calendar.

`quarterly_expiries`

:    Quarterly expiry days (quadruple witching). Typically observed on the third Friday of March, June, September, and
December, though some exchanges observe them on Thursday. Collisions with holidays or
special open/close days are usually resolved by rolling backward to the previous regular business day.

`monthly_expiries`

:   Monthly expiry days for all remaining months that do not have a quarterly expiry day. Provided in a separate
calendar as they typically result in less extreme trading patterns.

`last_session_of_months`

:   The last trading session for each month of the year.

`last_regular_session_of_months`

:   The last *regular* trading session for each month of the year, i.e. not a special open/close or otherwise irregular
day.

`tags`

:   Method to query day ranges for given tags. See [Tags](tags.md) for details.

## Aggregate calendars

The aggregate calendars `holidays_all`, `special_opens_all`, `special_closes_all` merge regular and ad-hoc entries
into a single calendar so you don't have to query multiple calendars on the underlying exchange calendar.

!!! note

    Aggregate calendars for special open/close days may combine days with different session times.
    The individual open/close time cannot be recovered from the aggregate calendars alone.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")
print(
    calendar.holidays_all.holidays(
        start="2020-01-01", end="2020-12-31", return_name=True
    )
)
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

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

NumPy's `NaN` indicates holidays without a specific name in
the [exchange-calendars](https://pypi.org/project/exchange-calendars/) model such as ad-hoc holidays. E.g. 2020-05-08 is
an ad-hoc holiday for XLON, the early May bank holiday was moved in honor of the 75th VE Day anniversary;
see [announcement](https://www.gov.uk/government/news/2020-may-bank-holiday-will-be-moved-to-mark-75th-anniversary-of-ve-day).

## Week and weekend days

The calendars `week_days` and `weekend_days` reflect the underlying weekmask of the exchange calendar. A week day is
usually a business day, but can also be a holiday. Weekend days are never business days, but can be holidays as well.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")
print(
    calendar.week_days.holidays(
        start="2020-01-01", end="2020-12-31"
    )
)
print(
    calendar.weekend_days.holidays(
        start="2020-01-01", end="2020-12-31"
    )
)
```

!!! note

    Calendars for week and weekend days, and some other additional calendars, do not provide names. Using
    `return_name=True` only makes sense if you specifically need a Pandas `Series` instead of a `DatetimeIndex`.

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
DatetimeIndex(['2020-01-01', '2020-01-02', '2020-01-03', '2020-01-06',
               '2020-01-07', '2020-01-08', '2020-01-09', '2020-01-10',
               '2020-01-13', '2020-01-14',
               ...
               '2020-12-18', '2020-12-21', '2020-12-22', '2020-12-23',
               '2020-12-24', '2020-12-25', '2020-12-28', '2020-12-29',
               '2020-12-30', '2020-12-31'],
              dtype='datetime64[us]', length=262, freq=None)
DatetimeIndex(['2020-01-04', '2020-01-05', '2020-01-11', '2020-01-12',
               '2020-01-18', '2020-01-19', '2020-01-25', '2020-01-26',
               '2020-02-01', '2020-02-02',
               ...
               '2020-11-28', '2020-11-29', '2020-12-05', '2020-12-06',
               '2020-12-12', '2020-12-13', '2020-12-19', '2020-12-20',
               '2020-12-26', '2020-12-27'],
              dtype='datetime64[us]', length=104, freq=None)
```

## Quarterly/monthly expiry days

Quarterly and monthly expiry calendars are available for [select exchanges](exchanges.md).

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")
print(calendar.quarterly_expiries.holidays(start="2023-01-01", end="2023-12-31"))
print(calendar.monthly_expiries.holidays(start="2023-01-01", end="2023-12-31"))
```

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
DatetimeIndex(['2023-03-17', '2023-06-16', '2023-09-15', '2023-12-15'], dtype='datetime64[us]', freq=None)
DatetimeIndex(['2023-01-20', '2023-02-17', '2023-04-21', '2023-05-19',
               '2023-07-21', '2023-08-18', '2023-10-20', '2023-11-17'],
              dtype='datetime64[us]', freq=None)
```

Expiry days do not provide names.

## Last trading days of months

Like the expiry day calendars, the last (regular) trading day of a month calendars do not provide names.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

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

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

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

Notice the difference in December: 2023-12-29 is a special close day on XLON, so 2023-12-28 is the last *regular*
trading day in that month.

These calendars also do not provide names.

## Tags

Tags are a completely new feature that let you attach arbitrary labels to days. As a consequence, no tags are present on
any calendar or days by default. They first need to be added through the changes API;
see [Calendar changes](changes.md).

Once added, tags can be retrieved using the `tags` method.

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

<div style="text-align: center;" markdown>:lucide-arrow-down:</div>

```text
2022-12-27       {foo, bar}
2022-12-28    {foo, foobar}
dtype: object
```

See the [Tags](tags.md) section for details.
