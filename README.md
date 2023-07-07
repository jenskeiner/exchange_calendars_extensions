# exchange-calendars-extensions
[![PyPI](https://img.shields.io/pypi/v/exchange-calendars-extensions)](https://pypi.org/project/exchange-calendars-extensions/) ![Python Support](https://img.shields.io/pypi/pyversions/exchange_calendars_extensions) ![PyPI Downloads](https://img.shields.io/pypi/dd/exchange-calendars-extensions)

A Python package that transparently adds some features to the [exchange-calendars](https://pypi.org/project/exchange-calendars/) 
package.

For all exchanges, this package adds the following:
- Calendars that combine existing regular and ad-hoc holidays or special open/close days into a single 
  calendar, respectively.
- Calendars for the last trading session of each month, and the last *regular* trading session of each month.
- The ability to modify exising calendars by adding or removing holidays, special open/close days, or others, 
  programmatically at runtime.

For select exchanges, this packages also adds:
- Calendars for additional special trading sessions, such as quarterly expiry days (aka quadruple witching).

## Combined calendars
This package adds combined calendars for holidays and special open/close days, respectively. These calendars combine 
regular with ad-hoc occurrences of each type of day. Note that for special open/close days, this may 
aggregate days with different open/close times into a single calendar. From the calendar, the open/close time for each 
contained day cannot be recovered.

## Additional calendars
In addition to information that is already available in 
[exchange-calendars](https://pypi.org/project/exchange-calendars/), this package also adds calendars for 
the following trading sessions:
- last trading session of the month, and
- last *regular* trading session of the month.

For select exchanges (see [below](#supported-exchanges)), this package also adds calendars for:
- quarterly expiry days (aka quadruple witching), and
- monthly expiry days (in all months without quarterly expiry day).

Finally, a new calendar that contains all weekend days as per the underlying weekmask is also available.

## Calendar modifications
This package also adds the ability to modify existing calendars at runtime. This can be used to add or remove
- holidays (regular and ad-hoc),
- special open days (regular and ad-hoc),
- special close days (regular and ad-hoc),
- quarterly expiry days, and
- monthly expiry days.

This is useful for example when an exchange announces a special trading session on short notice, or when the exchange 
announces a change to the regular trading schedule, and the next release of the exchange-calendars package may not be 
in time.

## Installation
The package is available on [PyPI](https://pypi.org/project/exchange-calendars-extensions/) and can be installed via 
[pip](https://pip.pypa.io/en/stable/) or any other suitable package/dependency management tool, e.g. 
[Poetry](https://python-poetry.org/).

```bash
pip install exchange-calendars-extensions
```

## Usage
Import the package and register extended exchange calendar classes with the `exchange_calendars` module.
```python
import exchange_calendars_extensions as ece

ece.apply_extensions()
```
This replaces the default exchange calendar classes with the extended versions. 

Get an exchange calendar instance and verify that extended exchange calendars are subclasses of the abstract base 
class `ece.ExtendedExchangeCalendar`. This class inherits both from 
`ec.ExchangeCalendar` and the new protocol class 
`ece.ExchangeCalendarExtensions` which defines the extended properties.

```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

calendar = ec.get_calendar('XLON')

assert isinstance(calendar, ece.ExtendedExchangeCalendar)
assert isinstance(calendar, ec.ExchangeCalendar)
assert isinstance(calendar, ece.ExchangeCalendarExtensions)
```

The original classes can be reinstated by calling `ece.remove_extensions()`.

```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

...

ece.remove_extensions()

calendar = ec.get_calendar('XLON')

assert not isinstance(calendar, ece.ExtendedExchangeCalendar)
assert isinstance(calendar, ec.ExchangeCalendar)
assert not isinstance(calendar, ece.ExchangeCalendarExtensions)
```

### Additional properties
Extended exchange calendars provide the following calendars as properties:
- `holidays_all`: Regular and ad-hoc holidays combined into a single calendar.
- `special_opens_all`: Regular and ad-hoc special open days combined into a single calendar.
- `special_closes_all`: Regular and ad-hoc special close days combined into a single calendar.
- `weekend_days`: All weekend days, as defined by the underlying weekmask, in a single calendar.
- `quarterly_expiries`: Quarterly expiry days, also known as quadruple witching. Many exchanges observe special business
  days on which market index futures, options futures, stock options and stock futures expire, typically resulting in 
  increased volatility and traded volume. Quadruple witching is typically observed on the third Friday of March, June,
  September and December, although some exchanges observe it on Thursday instead. Note that in the case of collisions 
  with holidays or special open/close days, a quarterly expiry day is usually rolled backward to the previous and 
  otherwise regular business day. 
- `monthly_expiries`: Monthly expiry days. Similar to quarterly expiry days, but for all remaining months of the year. 
  Provided in a separate calendar as they typically result in less extreme trading patterns.
- `last_session_of_months`: The last trading session for each month of the year.
- `last_regular_session_of_months`: Last regular trading session of each month of the year, i.e. not a special 
  open/close or otherwise irregular day.

```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

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
Note that the ad-hoc holiday on 2020-05-08 (Queen Elizabeth II 75th anniversary) is included in the holiday calendar, 
even though it is not a regular holiday.

Quarterly and monthly expiry days:
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

calendar = ec.get_calendar('XLON')
print(calendar.quarterly_expiries.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
print(calendar.monthly_expiries.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
```
will output
```text
2023-03-17    quarterly expiry
2023-06-16    quarterly expiry
2023-09-15    quarterly expiry
2023-12-15    quarterly expiry
dtype: object
2023-01-20    monthly expiry
2023-02-17    monthly expiry
2023-04-21    monthly expiry
2023-05-19    monthly expiry
2023-07-21    monthly expiry
2023-08-18    monthly expiry
2023-10-20    monthly expiry
2023-11-17    monthly expiry
dtype: object
```

Last trading days of months:
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec


calendar = ec.get_calendar('XLON')
print(calendar.last_trading_days_of_months.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
print(calendar.last_regular_trading_days_of_months.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
```
will output
```text
2023-01-31    last trading day of month
2023-02-28    last trading day of month
2023-03-31    last trading day of month
2023-04-28    last trading day of month
2023-05-31    last trading day of month
2023-06-30    last trading day of month
2023-07-31    last trading day of month
2023-08-31    last trading day of month
2023-09-29    last trading day of month
2023-10-31    last trading day of month
2023-11-30    last trading day of month
2023-12-29    last trading day of month
dtype: object
2023-01-31    last regular trading day of month
2023-02-28    last regular trading day of month
2023-03-31    last regular trading day of month
2023-04-28    last regular trading day of month
2023-05-31    last regular trading day of month
2023-06-30    last regular trading day of month
2023-07-31    last regular trading day of month
2023-08-31    last regular trading day of month
2023-09-29    last regular trading day of month
2023-10-31    last regular trading day of month
2023-11-30    last regular trading day of month
2023-12-28    last regular trading day of month
dtype: object
```
Note the difference in December, where 2023-12-29 is a special close day, while 2023-12-28 is a regular trading day.

### Adding/removing holidays and special sessions
The extended classes provide methods of the form 
`{add,remove}_{holiday,special_open,special_close,quarterly_expiry,monthly_expiry}(...)`at the package level to add or 
remove certain holidays or special sessions programmatically. For example,

```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_holiday('XLON', '2022-12-28', 'Holiday')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.regular_holidays.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()
```
will add a new holiday named `Holiday` to the calendar for the London Stock Exchange on 28 December 2022. Similarly,
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.remove_holiday('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.regular_holidays.holidays()
assert '2022-12-27' not in calendar.holidays_all.holidays()
```
will remove the holiday on 27 December 2022 from the calendar.

To specify the date, you can use anything that can be converted into a valid `pandas.Timestamp`. This includes strings
in the format `YYYY-MM-DD`, `datetime.date` objects, or `pandas.Timestamp` objects. The name of the holiday can be any
string.

Holidays are always added as regular holidays to allow for an individual name. Removing holidays works for both regular
and ad-hoc holidays, regardless whether the affected days are in the original calendar or have been added 
programmatically at an earlier stage.

Whenever a calendar has been modified programmatically, the changes are only reflected after obtaining a new exchange 
calendar instance.
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

calendar = ec.get_calendar('XLON')

# Unchanged calendar.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()

# Modify calendar. Clears the cache, so ec.get_calendar('XLON') will return a new instance next time.
ece.add_holiday('XLON', '2022-12-28', 'Holiday')
ece.remove_holiday('XLON', '2022-12-27')

# Changes not reflected in existing instance.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()

# Get new instance.
calendar = ec.get_calendar('XLON')

# Changes reflected in new instance.
assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()

# Revert the changes.
ece.remove_holiday('XLON', '2022-12-28')
ece.add_holiday('XLON', '2022-12-27', 'Weekend Christmas')

# Get new instance.
calendar = ec.get_calendar('XLON')

# Changes reverted in new instance.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()
```

It is possible to add or remove holidays, special open/close days, and quarterly/monthly expiries. Adding special 
open/close days requires to specify the open/close time in addition to the date.
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

calendar = ec.get_calendar('XLON')

assert '2022-12-28' not in calendar.special_opens_all.holidays()

ece.add_special_open('XLON', '2022-12-28', '11:00', 'Special Open')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.special_opens_all.holidays()
```

The open/close time can be in the format `HH:MM` or `HH:MM:SS`, or a `datetime.time` object.

The ennumeration `DayType` can be used to add or remove holidays in a more generic way.

```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_day('XLON', '2022-12-28', {'name': 'Special Open', 'time': '11:00'}, ece.DayType.SPECIAL_OPEN)

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.special_opens_all.holidays()

ece.remove_day('XLON', '2022-12-28', ece.DayType.SPECIAL_OPEN)

calendar = ec.get_calendar('XLON')

assert '2022-12-28' not in calendar.special_opens_all.holidays()
```

When removing a day, the day type is optional. In this case, the day is just removed for all day types. 
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_day('XLON', '2022-12-28', {'name': 'Special Open', 'time': '11:00'}, ece.DayType.SPECIAL_OPEN)

calendar = ec.get_calendar('XLON')

assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.special_opens_all.holidays()

ece.remove_day('XLON', '2022-12-27')
ece.remove_day('XLON', '2022-12-28')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.special_opens_all.holidays()
```
This is useful to ensure that a given day does not mark a holiday or any special session. Note that a day could still be
a weekend day and that removing the day does not change it into a business day.

### Reverting changes

It is sometimes necessary to revert individual changes made to a calendar such as adding or removing holidays or special
sessions. To that end, the package provides the methods of the form 
`reset_{holiday,special_open,special_close,quarterly_expiry,monthly_expiry}(...)` at the package level.

```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_holiday('XLON', '2022-12-28', 'Holiday')
ece.remove_holiday('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()

ece.reset_holiday('XLON', '2022-12-28')
ece.reset_holiday('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

# Calendar unchanged again.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()
```

The is also a more generic method `reset_day(...)` that can be used to reset a day for a given day type. Again, 
`day_type` is optional and omitting the argument will just reset the day for all day types.
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_holiday('XLON', '2022-12-28', 'Holiday')
ece.remove_holiday('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()

ece.reset_day('XLON', '2022-12-27', ece.DayType.HOLIDAY)
ece.reset_day('XLON', '2022-12-28')

calendar = ec.get_calendar('XLON')

# Calendar unchanged again.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()
```

To reset an entire calendar to its original state, use the method `reset_calendar(...)`.

```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_holiday('XLON', '2022-12-28', 'Holiday')
ece.remove_holiday('XLON', '2022-12-27')

calendar = ec.get_calendar('XLON')

assert '2022-12-27' not in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()

ece.reset_calendar('XLON')

calendar = ec.get_calendar('XLON')

# Calendar unchanged again.
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' not in calendar.holidays_all.holidays()
```


### Strict mode

Removing a day is always handled gracefully when the day is not already present as a special day in the calendar, i.e. 
this does not throw an exception. In contrast, the same day cannot be added for multiple day types at the same time. By default, this 
is also handled gracefully by keeping just the last definition in place.

This default behavior may sometimes be inadequate, e.g. when it is important to enforce consistency of all applied 
changes. For example, the following code will not throw an exception:
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_day('XLON', '2022-12-28', {'name': 'Special Open', 'time': '11:00'}, ece.DayType.SPECIAL_OPEN)
ece.add_day('XLON', '2022-12-28', {'name': 'Special Close', 'time': '12:00'}, ece.DayType.SPECIAL_CLOSE)

c = ec.get_calendar('XLON')

assert '2022-12-28' not in c.special_opens_all.holidays()
assert '2022-12-28' in c.special_closes_all.holidays()
```

This is because the default behavior keeps the special close day that supersedes the special open day.

To enforce consistency of all changes at any stage, the optional keyword argument `strict` maybe be set to `True`. For 
example,
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_day('XLON', '2022-12-28', {'name': 'Special Open', 'time': '11:00'}, ece.DayType.SPECIAL_OPEN, strict=True)
ece.add_day('XLON', '2022-12-28', {'name': 'Special Close', 'time': '12:00'}, ece.DayType.SPECIAL_CLOSE, strict=True)

c = ec.get_calendar('XLON')
```
will throw `ValidationError` when the same day is added a second time for a different day types. The same is true when 
the same day is added and removed for the same day type.
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

ece.add_day('XLON', '2022-12-28', {'name': 'Special Open', 'time': '11:00'}, ece.DayType.SPECIAL_OPEN, strict=True)
ece.remove_day('XLON', '2022-12-28', ece.DayType.SPECIAL_OPEN, strict=True)

c = ec.get_calendar('XLON')
```

### Changesets

Internally, whenever a calendar for an exchange is modified through a call to an appropriate function, the resulting 
changes are accumulated in a changeset, i.e. a collection of zero or more changes, that are specific to that exchange. 
That is, subsequent calls for the same exchange will update the same changeset. 

When a new exchange calendar instance is created, the changes from the corresponding changeset are applied to the 
underlying and still unmodified exchange calendar. This is why a new fresh instance of a calendar needs to be obtained 
to reflect any previously made changes. 

As a user, you don't need to interact with changesets directly, but it is important to understand the concept to
understand the behavior of this package.

Changesets have a notion of consistency. A changeset is consistent if and only if the following conditions are satisfied:
1) For each day type, the corresponding dates to add and dates to remove do not overlap.
2) For each distinct pair of day types, the dates to add do not overlap.

The first condition ensures that the same day is not added and removed at the same time for the same day type. The 
second condition ensures that the same day is not added for two different day types. Note that marking the same day as
a day to remove is valid for multiple day types at the same time since this it will be a no-op if the day is not 
actually present in the calendar for a day type.

In essence, consistency ensures that the changes in a changeset do not contradict each other.

By default, any call to a function that modifies a calendar will ensure that the resulting changeset is consistent, as
described above. This can be disabled by setting the optional keyword argument `strict` to `False`. In this case, the 
function throws an exception if the resulting changeset would become inconsistent. The underlying changeset remains in 
the last consistent state. 


### Applying changesets to a calendar

In certain scenarios, it may be desirable to apply an entire set of changes to an exchange calendar. For example, the 
changes could be read from a file or a database. This can be achieved using the `update_calendar(...)` function. For 
example,
```python
import exchange_calendars_extensions as ece
ece.apply_extensions()
import exchange_calendars as ec

changes = {
    "holiday": {
        "add": {"2022-01-10": {"name": "Holiday"}}, 
        "remove": ["2022-01-11"]
    },
    "special_open": {
        "add": {"2022-01-12": {"name": "Special Open", "time": "10:00"}}, 
        "remove": ["2022-01-13"]
    },
    "special_close": {
        "add": {"2022-01-14": {"name": "Special Close", "time": "16:00"}}, 
        "remove": ["2022-01-17"]
    },
    "monthly_expiry": {
        "add": {"2022-01-18": {"name": "Monthly Expiry"}}, 
        "remove": ["2022-01-19"]
    },
    "quarterly_expiry": {
        "add": {"2022-01-20": {"name": "Quarterly Expiry"}}, 
        "remove": ["2022-01-21"]
    }
}

ece.update_calendar('XLON', changes)

calendar = ec.get_calendar('XLON')

assert '2022-01-10' in calendar.holidays_all.holidays()
assert '2022-01-11' not in calendar.holidays_all.holidays()
assert '2022-01-12' in calendar.special_opens_all.holidays()
assert '2022-01-13' not in calendar.special_opens_all.holidays()
assert '2022-01-14' in calendar.special_closes_all.holidays()
assert '2022-01-17' not in calendar.special_closes_all.holidays()
assert '2022-01-18' in calendar.monthly_expiries.holidays()
assert '2022-01-19' not in calendar.monthly_expiries.holidays()
assert '2022-01-20' in calendar.quarterly_expiries.holidays()
assert '2022-01-21' not in calendar.quarterly_expiries.holidays()
```


### Normalization
A changeset needs to be consistent before it can be applied to an exchange calendar. However, consistency alone is not 
enough to ensure that an exchange calendar with a changeset applied is itself consistent. The reason this can happen is 
that a changeset e.g. may add a holiday, but the unmodified exchange calendar may already contain the same day as a 
special open day. This is to say that the resulting calendar would contain the same day with two different, but mutually 
exclusive, day types.

To ensure that an exchange calendar with a changeset applied is consistent, the changeset is normalized before it is 
applied. Normalization ensures that the same day can only be contained with one day type in the resulting exchange 
calendar. This is achieved by augmenting the changeset before it is applied to remove any day that is added with one day
type from all other day types. For example, this means that if a day is a holiday in the original exchange calendar, but
the changeset adds the same day as a special open day, the resulting calendar will contain the day as a special open 
day. In essence, adding days may overwrite the day type if the original calendar already contained the same day.

Normalization happens transparently to the user, this section is only included to explain the rationale behind it. 
Ensuring consistency of a changeset is enough to make it compatible with any exchange calendar, owing to the 
normalization behind the scenes.

### Reading changesets from dictionaries.
Entire changesets can be applied to an exchange calendar can be imported through appropriately structured
dictionaries. This enables reading and then applying entire collections of changes from files and other sources.
```python
from exchange_calendars_extensions import update_calendar
from exchange_calendars_extensions import get_calendar

changes = {
    "holiday": {
        "add": [{"date": "2020-01-01", "value": {"name": "Holiday"}}], 
        "remove": ["2020-01-02"]
    },
    "special_open": {
        "add": [{"date": "2020-02-01", "value": {"name": "Special Open", "time": "10:00"}}], 
        "remove": ["2020-02-02"]
    },
    "special_close": {
        "add": [{"date": "2020-03-01", "value": {"name": "Special Close", "time": "16:00"}}], 
        "remove": ["2020-03-02"]
    },
    "monthly_expiry": {
        "add": [{"date": "2020-04-01", "value": {"name": "Monthly Expiry"}}], 
        "remove": ["2020-04-02"]
    },
    "quarterly_expiry": {
        "add": [{"date": "2020-05-01", "value": {"name": "Quarterly Expiry"}}], 
        "remove": ["2020-05-02"]
    }
}

update_calendar('XLON', changes)

calendar = get_calendar('XLON')
# Calendar now contains the changes from the dictionary.
```
The above example lays out the complete schema that is expected for obtaining a changeset from a dictionary. Instead of 
dates in ISO format, `pandas.Timestamp` instances may be used. Similarly, wall-clock times may be specified
as `datetime.time` instances. SO, the following woulw work as well:
```python
update_calendar('XLON', {
    'special_open': {
        'add': [{"date": pd.Timestamp("2020-02-01"), "value": {"name": "Special Open", "time": dt.time(10, 0)}}]
    }
})
```

Updating an exchange calendar from a dictionary removes any previous changes that have been recorded, i.e. the incoming
changes are not merged with the existing ones. This is to ensure that the resulting calendar is consistent. Of course,
the incoming changes must result in a consistent changeset themselves or an exception will be raised.

A use case for updating an exchange calendar from a dictionary is to read changes from a file. The following example
reads changes from a JSON file and applies them to the exchange calendar.
```python
import json

with open('changes.json', 'r') as f:
    changes = json.load(f)
    
update_calendar('XLON', changes)
```

## Supported exchanges for monthly/quarterly expiry
This package currently provides support for monthly/querterly expiry calendars for the following subset of exchanges 
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
sub-module `exchange_calendars_extensions.holiday_calendar`.
```python
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars_extensions.holiday_calendar import extend_class

xlon_extended_cls = extend_class(XLONExchangeCalendar, day_of_week_expiry=4)
```
The first argument to `extend_class` should be the class of the exchange calendar to extend. The second and optional
parameter, which defaults to `None`, is the day of the week on which expiry days are normally observed. If this parameter 
is `None`, this assumes that the underlying exchange does not support monthly or quarterly expiry days and the respective
calendars will not be added.

The returned extended class directly inherits from the passed base class and adds the additional attributes like 
`holidays_all` et cetera. The returned class also supports programmatic modifications using the corresponding exchange 
key of the parent class.

To register a new extended class for an exchange, use the `register_extension()` function before calling 
`apply_extensions()`.
```python
from exchange_calendars_extensions import register_extension, apply_extensions

register_extension(key, cls)
apply_extensions()
...
```
Here, `key` should be the name, i.e. not an alias, under which the extended class is registered with the 
`exchange_calendars` package, and `cls` should be the extended class.

## Caveat: Merging calendars
For the various calendars, [exchange-calendars](https://pypi.org/project/exchange-calendars/) defines and uses the class
`exchange_calendars.exchange_calendar.HolidayCalendar` which is a direct subclass of the abstract base class
`pandas.tseries.holiday.AbstractHolidayCalendar`.

One of the assumptions of `AbstractHolidayCalendar` is that each contained rule that defines a holiday has a unique name.
Thus, when merging two calendars via the `.merge()` method, the resulting calendar will only retain a single rule for
each name, eliminating any duplicates.

This creates a problem with the calendars provided by this package. For example, constructing the holiday calendar 
backing `holidays_all` requires to add a rule for each ad-hoc holiday. However, since ad-hoc holidays don't define a 
unique name, each rule would either have to generate a unique name for itself, or use the same name as the other rules. 
This package uses the latter approach, i.e. all ad-hoc holidays are assigned the same name `ad-hoc holiday`.

As a result, the built-in merge functionality of `AbstractHolidayCalendar` will eliminate all but one of the ad-hoc 
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
