---
title: "Calendar Modifications"
draft: false
type: docs
layout: "single"

menu:
  docs_extensions:
      weight: 50
---
# Calendar Modifications

Extended exchange calendars provide an API to support modifications at runtime. 

## Dates, Times, and Day Types
Calendar modifications are represented using common data types for dates, wall-clock times, and types of special 
days. Thanks to Pydantic and custom annotated types, however, the API allows to pass in values in different formats that
will safely be converted into the correct used internally.

Wherever the API expects a `pandas.Timestamp`, represented by the type `TimestampLike`, it is possible to an actual 
`pandas.Timestamp`, a `datetime.date` object, a string in ISO format `YYYY-MM-DD`, or any other valid value that can be 
used to initialize a timestamp. Pydantic will validate such calls and enforce the correct data type.

There is also the special type `DateLike` which is used to represent date-like Timestamps. Such timestamps are 
normalized to midnight and are timezone-naive. They represent full days starting at midnight (inclusive) and ending at 
midnight (exclusive) of the following day *in the context of the exchange and the corresponding timezone they are used 
in*. A `DateLike` timestamp is typically used to specify a date for a specific exchange calendar that has a timezone 
attached.

Similar to timestamps, wall clock times in the form of `datetime.time` are represented by 
`TimeLike` to allow passing an actual `datetime.time` or strings in the format 
`HH:MM:SS` or `HH:MM`.

The enumeration type `DayType` represents types of special days, API calls accept either enumeration members or 
their string value. For example, `DayType.HOLIDAY` and `'holiday'` can be used equivalently.

## Adding Special Days

The `exchange_calendars_extensions` module provides the following methods for adding special days:

- `add_holiday`: Adds a single regular holiday.
- `add_special_open`: Adds a single special open day.
- `add_special_close`: Adds a single special close day.
- `add_monthly_expiry`: Adds a single monthly expiry day.
- `add_quarterly_expiry`: Adds a single quarterly expiry day.

For example,
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.regular_holidays.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()
```
will add a new holiday named `Holiday` to the calendar for the London Stock Exchange on 28 December 2022. Holidays are 
always added as regular holidays, not as ad-hoc holidays, to allow for an individual name.

Adding special open or close days works similarly, but needs the respective special open or close time:
```python
import exchange_calendars_extensions.core as ecx

ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_special_open('XLON', date='2022-12-28', time='11:00', name='Special Open')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.special_opens_all.holidays()
```

A more generic way to add a special day is via `add_day(...)` which takes either a `DaySpec` (holidays, 
monthly/quarterly expiries) or `DaySpecWithTime` (special open/close days) Pydantic model:
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_day('XLON', ecx.DaySpec(date='2022-12-27', type=ecx.DayType.HOLIDAY, name='Holiday'))
ecx.add_day('XLON', ecx.DaySpecWithTime(date='2022-12-28', type=ecx.DayType.SPECIAL_OPEN, name='Special Open', time='11:00'))

calendar = ec.get_calendar('XLON')

assert '2022-12-27' in calendar.regular_holidays.holidays()
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.special_opens_all.holidays()
```

The `DayType` enum enumerates all supported special day types.

Thanks to Pydantic, an even easier way just uses suitable dictionaries: 
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_day('XLON', {'date': '2022-12-27', 'type': 'holiday', 'name': 'Holiday'})
ecx.add_day('XLON', {'date': '2022-12-28', 'type': 'special_open', 'name': 'Special Open', 'time': '11:00'})

calendar = ec.get_calendar('XLON')

assert '2022-12-27' in calendar.regular_holidays.holidays()
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.special_opens_all.holidays()
```
The dictionary format makes it particularly easy to read in changes from an external source like a file.

## Removing Special Days

To remove a day as a special day (of any type) from a calendar, use `remove_day`. For example,
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.remove_day('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.regular_holidays.holidays()
assert '2022-12-27' not in calendar.holidays_all.holidays()
```
will remove the holiday on 27 December 2022 from the calendar, thus turning this day into a regular trading day.

Removing a day via `remove_day(...)` that is not actually a special day, results in no change and does not throw an 
exception.

## Visibility of Changes
Whenever a calendar has been modified programmatically, the changes are only reflected after obtaining a new exchange 
calendar instance.
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

calendar = ec.get_calendar('XLON')

# Unchanged calendar.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()

# Modify calendar. This clears the cache, so ec.get_calendar('XLON') will return a new instance next time.
ecx.add_holiday('XLON', '2022-12-28', 'Holiday')
ecx.remove_day('XLON', '2022-12-27')

# Changes not reflected in existing instance.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()

# Get new instance.
calendar = ec.get_calendar('XLON')

# Changes reflected in new instance.
assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()

# Revert the changes.
ecx.reset_calendar('XLON')

# Get new instance.
calendar = ec.get_calendar('XLON')

# Changes reverted in new instance.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()
```

## Changesets
When modifying an exchange calendar, the changes are recorded in an `ecx.ChangeSet` associated with the corresponding 
exchange. When a new calendar instance is created, the changes are applied to the calendar, as seen above.

It is also possible to create a changeset separately and then associate it with a particular exchange:
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

changeset: ecx.ChangeSet = ecx.ChangeSet()
changeset.add_day({'date': '2022-12-28', 'type': 'holiday', 'name': 'Holiday'})
changeset.remove_day('2022-12-27')

ecx.update_calendar('XLON', changeset)

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()
```
Again, an entire changeset can also be created from a suitably formatted dictionary, making it particularly easy to read
in and apply changes from an external source like a file.
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

changeset: ecx.ChangeSet = ecx.ChangeSet(**{
    'add': [{'date': '2022-12-28', 'type': 'holiday', 'name': 'Holiday'}], 
    'remove': ['2022-12-27']})

ecx.update_calendar('XLON', changeset)

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()
```

## Adding and Removing the Same Day

The API permits to add and remove the same day as a special day. For example, the following code will add a holiday on
28 December 2022 to the calendar, and then remove the same day as well.
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')
ecx.remove_day('XLON', date='2022-12-28')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.holidays_all.holidays()
```
The result is that the day is a holiday in the changed calendar. These semantics of the API may be surprising, but make 
more sense in a case where a day is added to change its type of special day. Consider the date `2022-12-27` which is a 
holiday for the calendar `XLON` in the original version of the calendar. The following code will change the type of 
special day to a special open by first removing the day (as a holiday), and then adding it back as a special open day:
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.remove_day('XLON', date='2022-12-27')
ecx.add_special_open('XLON', date='2022-12-27', name='Special Open', time='11:00')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-27' in calendar.special_opens_all.holidays()
```
Removing a day does not consider the type of special day and thus will convert any type of special day into a regular
trading day (if the weekmask permits). Adding a day will add it as the specified type of special day. Together, this 
allows to change the type of special day in an existing calendar from one to another.

In fact, internally, each added days is always implicitly also removed from the calendar first, so that it strictly is 
not necessary (but allowed) to explicitly remove a day, and then adding it back as a different type of special day:
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

# It is enough to add an existing special day with a new type to change the type of special day.
ecx.add_special_open('XLON', date='2022-12-27', name='Special Open', time='11:00')

calendar = ec.get_calendar('XLON')

# No longer a holiday.
assert '2022-12-27' not in calendar.holidays_all.holidays()
# Now a special open.
assert '2022-12-27' in calendar.special_opens_all.holidays()
```

## Changeset Consistency
As seen above, changesets may contain the same day both in the list of days to add and in the list of days to remove.
However, changesets enforce consistency and will raise an exception if the same day is added more than once.
For example, the following code will raise an exception:
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')
ecx.add_special_open('XLON', date='2022-12-28', name='Special Open', time='11:00')
```
In contrast, removing a day is an idempotent operation, i.e. doing it twice will not raise an exception and keep the 
corresponding changeset the same as after the first removal. 
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()

ecx.remove_day('XLON', date='2022-12-27')
ecx.remove_day('XLON', date='2022-12-27')
```

## Reverting Changes

It is sometimes necessary to revert individual changes made to a calendar. To that end the package provides the method 
`reset_day`:

```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_holiday('XLON', '2022-12-28', 'Holiday')
ecx.remove_day('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()

ecx.reset_day('XLON', '2022-12-28')
ecx.reset_day('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

# Calendar unchanged again.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()
```

To reset an entire calendar to its original state, use the method `reset_calendar` or update the calendar with an 
empty ChangeSet:
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_holiday('XLON', '2022-12-28', 'Holiday')
ecx.remove_day('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()

# Same as ecx.update_calendar('XLON', ecx.ChangeSet())
ecx.reset_calendar('XLON')

calendar = ec.get_calendar('XLON')

# Calendar unchanged again.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()
```

## Retrieving Changes
For any calendar, it is possible to retrieve a copy of the associated changeset:
```python
import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')
ecx.remove_day('XLON', date='2022-12-27')

changeset: ecx.ChangeSet = ecx.get_changes_for_calendar('XLON')
print(changeset)
```

Output:
```text
add=[DaySpec(date=Timestamp('2022-12-28 00:00:00'), 
             name='Holiday', 
             type=<DayType.HOLIDAY: 'holiday'>)] 
remove=[Timestamp('2022-12-27 00:00:00')]
```

Since `ecx.get_changes_for_calendar` returns a copy of the changeset, any modifications to the returned changeset
will not affect the calendar.

To get the changesets for all calendars, use `ecx.get_changes_for_all_calendars`. This returns a dictionary that 
maps the exchange name/key to a copy of the corresponding changeset. 
