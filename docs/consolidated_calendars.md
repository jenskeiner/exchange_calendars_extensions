---
title: "Consolidated Calendars"
draft: false
type: docs
layout: "single"

menu:
  docs_extensions:
      weight: 30
---
# Consolidated Calendars
Extended exchange calendars provide consolidated calendars for holidays and special open/close days that include regular
and ad-hoc occurrences.

## Holidays
The consolidated calendar for holidays includes all regular and ad-hoc holidays. For example:
```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XLON')
print(calendar.holidays_all.holidays(start='2020-01-01', end='2020-12-31', return_name=True))
```
will output
```text
2020-01-01         New Year's Day
2020-04-10            Good Friday
2020-04-13          Easter Monday
2020-05-08         ad-hoc holiday
2020-05-25    Spring Bank Holiday
2020-08-31    Summer Bank Holiday
2020-12-25              Christmas
2020-12-26             Boxing Day
2020-12-28     Weekend Boxing Day
dtype: object
```
Note that the ad-hoc holiday on 2020-05-08 (Queen Elizabeth II 75th anniversary) is included together with all regular
holidays during the period.

In contrast, the standard calendar only includes regular holidays:
```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XLON')
print(calendar.holidays.holidays(start='2020-01-01', end='2020-12-31', return_name=True))
```
will output
```text
2020-01-01         New Year's Day
2020-04-10            Good Friday
2020-04-13          Easter Monday
2020-05-25    Spring Bank Holiday
2020-08-31    Summer Bank Holiday
2020-12-25              Christmas
2020-12-26             Boxing Day
2020-12-28     Weekend Boxing Day
dtype: object
```
Note that the ad-hoc holiday on 2020-05-08 is missing.

## Special Open/Close Days

Similar to holidays, consolidated calendars for special open/close days include all regular and ad-hoc occurrences.
```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XDUB')
print(calendar.special_closes_all.holidays(start='2018-01-01', end='2018-12-31', return_name=True))
```
The result is
```text
2018-03-01                 ad-hoc special close
2018-12-24    Last Trading Day Before Christmas
2018-12-31    Last Trading Day Of Calendar Year
dtype: object
```
which includes an ad-hoc special close day on 2018-03-01.

{{% note %}}
Depending on the exchange, the consolidated calendars for special open/close days may aggregate days with different
open/close times into a single calendar. It is currently not possible to recover the open/close time for a day from a
consolidated calendar.
{{% /note %}}

As another example, consider special close days for the Tel Aviv Stock Exchange (XTAE):
```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XTAE')
print(calendar.special_closes_all.holidays(start='2020-04-01', end='2020-4-30', return_name=True))
```
which gives
```text
2020-04-05           special close
2020-04-12    Passover Interim Day
2020-04-13    Passover Interim Day
2020-04-19           special close
2020-04-26           special close
dtype: object
```

This list contains regular special close days on Sundays where the exchange closes at 15:40 local time, as well as
regular special close days during Passover festivities where the exchange closes at 14:15 local time.
