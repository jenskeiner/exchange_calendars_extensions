# exchange-calendars-extensions
[![PyPI](https://img.shields.io/pypi/v/exchange-calendars-extensions)](https://pypi.org/project/exchange-calendars-extensions/) ![Python Support](https://img.shields.io/pypi/pyversions/exchange_calendars_extensions) ![PyPI Downloads](https://img.shields.io/pypi/dd/exchange-calendars-extensions)

A Python package that transparently adds some features to the [exchange-calendars](https://pypi.org/project/exchange-calendars/) 
package.

For all exchanges, this package adds the following:
- Calendars that combine existing regular and ad-hoc holidays/special open days/special close days into a single 
  calendar, respectively.
- Calendars for the last trading session of each month, and the last *regular* trading session of each month.
- The ability to modify existing calendars by adding or removing special days programmatically at runtime.

For select exchanges, this packages also adds:
- Calendars for additional special trading sessions, such as monthly and quarterly expiry days (aka quadruple witching).
- The ability to add or remove these additional special trading sessions programmatically at runtime.

## Combined calendars
This package adds combined calendars for holidays and special open/close days, respectively. These calendars combine 
regular with ad-hoc occurrences.

Note that for special open/close days, this may aggregate days with different 
open/close times into a single calendar. From the combined calendar, the open/close time for each contained day cannot 
be recovered.

## Additional calendars
In addition to information that is already available in 
[exchange-calendars](https://pypi.org/project/exchange-calendars/), this package also adds calendars for 
the following trading sessions:
- last trading session of the month, and
- last *regular* trading session of the month.

For select exchanges (see [below](#supported-exchanges-for-monthlyquarterly-expiry)), this package also adds calendars for:
- quarterly expiry days (aka quadruple witching), and
- monthly expiry days (in all remaining months that don't have a quarterly expiry day).

Finally, a new calendar that contains all weekend days as per the underlying weekmask is also available.

## Calendar modifications
This package also adds the ability to modify existing calendars at runtime. This can be used to add or remove
- holidays (regular and ad-hoc),
- special open days (regular and ad-hoc),
- special close days (regular and ad-hoc),
- quarterly expiry days, and
- monthly expiry days.

This is useful, for example, when an exchange announces a change to the regular trading schedule on short notice, and 
the next release of the `exchange-calendars` package, including these changes, is not available yet.

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
import exchange_calendars_extensions as ecx

ecx.apply_extensions()
```
This replaces the default exchange calendar classes with the extended versions. 

Get an exchange calendar instance and verify that extended exchange calendars are subclasses of the abstract base 
class `ecx.ExtendedExchangeCalendar`. This class inherits both from 
`ec.ExchangeCalendar` and the new protocol class 
`ecx.ExchangeCalendarExtensions` which defines the extended properties.

```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
import exchange_calendars as ec

calendar = ec.get_calendar('XLON')

# It's still a regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# But it's also an extended exchange calendar...
assert isinstance(calendar, ecx.ExtendedExchangeCalendar)
# ...and implements the extended protocol.
assert isinstance(calendar, ecx.ExchangeCalendarExtensions)
```

The original classes can be re-instated by calling `ecx.remove_extensions()`.

```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
import exchange_calendars as ec

...

ecx.remove_extensions()

calendar = ec.get_calendar('XLON')

# It's a regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# But it's not an extended exchange calendar anymore.
assert not isinstance(calendar, ecx.ExtendedExchangeCalendar)
assert not isinstance(calendar, ecx.ExchangeCalendarExtensions)
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

For example,
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
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
Note that the ad-hoc holiday on 2020-05-08 (Queen Elizabeth II 75th anniversary) is included in the combined holiday 
calendar, together with all regular holidays during the period.

Quarterly and monthly expiry days:
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
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
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
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
Note the difference in December, where 2023-12-29 is a special close day, so 2023-12-28 is the last regular trading day
in that month.

### Adding special days

The `exchange_calendars_extensions` module provides the methods `add_holiday(...)`, `add_special_open(...)`, 
`add_special_close(...)`, `add_monthly_expiry(...)` and `add_quarterly_expiry(...)` to add holidays and other types of 
special days. For example,
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.regular_holidays.holidays()
assert '2022-12-28' in calendar.holidays_all.holidays()
```
will add a new holiday named `Holiday` to the calendar for the London Stock Exchange on 28 December 2022. Holidays are 
always added as regular holidays to allow for an individual name.

Adding special open or close days works similarly, but needs the respective special open or close time:
```python
import exchange_calendars_extensions as ecx

ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_special_open('XLON', date='2022-12-28', time='11:00', name='Special Open')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.special_opens_all.holidays()
```

A more generic way to add a special day is via `add_day(...)` which takes either a `DaySpec` (holidays, 
monthly/quarterly expiries) or `DaySpecWithTime` (special open/close days) Pydantic model:
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_day('XLON', ecx.DaySpec(date='2022-12-27', type=ecx.DayType.HOLIDAY, name='Holiday'))
ecx.add_day('XLON', ecx.DaySpecWithTime(date='2022-12-28', type=ecx.DayType.SPECIAL_OPEN, name='Special Open', time='11:00'))

calendar = ec.get_calendar('XLON')

assert '2022-12-27' in calendar.regular_holidays.holidays()
assert '2022-12-27' in calendar.holidays_all.holidays()
assert '2022-12-28' in calendar.special_opens_all.holidays()
```

Thanks to Pydantic, an even easier way is to just use suitable dictionaries: 
```python
import exchange_calendars_extensions as ecx
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

### Removing special sessions

To remove a day as a special day (of any type) from a calendar, use `remove_day(...)`. For example,
```python
import exchange_calendars_extensions as ecx
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

### Specifying dates, times, and day types
Thanks to Pydantic, dates, times, and the types of special day can typically be specified in different formats and will 
safely be parsed into the correct data type that is used internally.

For example, wherever the API expects a date, you may pass in a `pandas.Timestamp`, a `datetime.date` object, or simply
a string in ISO format `YYYY-MM-DD`. Similarly, wall clock times can be passed as `datetime.time` objects or as strings 
in the format `HH:MM:SS` or `HH:MM`.

The enumeration type `ecx.DayType` represents types of special days, API calls accept either enumeration members or 
their string value. For example, `ecx.DayType.HOLIDAY` and `'holiday'` are equivalent.

### Change visibility
Whenever a calendar has been modified programmatically, the changes are only reflected after obtaining a new exchange 
calendar instance.
```python
import exchange_calendars_extensions as ecx
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

### Changesets
When modifying an exchange calendar, the changes are recorded in an `ecx.ChangeSet` associated with the corresponding 
exchange. When a new calendar instance is created, the changes are applied to the calendar, as seen above.

It is also possible to create a changeset separately and then associate it with a particular exchange:
```python
import exchange_calendars_extensions as ecx
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
import exchange_calendars_extensions as ecx
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

### Adding and removing the same day

The API permits to add and remove the same day as a special day. For example, the following code will add a holiday on
28 December 2022 to the calendar, and then remove the same day as well.
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()
import exchange_calendars as ec

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')
ecx.remove_day('XLON', date='2022-12-28')

calendar = ec.get_calendar('XLON')

assert '2022-12-28' in calendar.holidays_all.holidays()
```
The result is that the day is a holiday in the changed calendar. These semantics of the API may be surprising, but make 
more sense in a case where a day is added to change its type of special day. Consider the date `2022-12-27` which was a 
holiday for the calendar `XLON` in the original version of the calendar. The following code will change the type of 
special day to a special open by first removing the day (as a holiday), and then adding it back as a special open day:
```python
import exchange_calendars_extensions as ecx
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
import exchange_calendars_extensions as ecx
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

### Changeset consistency
As seen above, changesets may contain the same day both in the list of days to add and in the list of days to remove.
However, changesets enforce consistency and will raise an exception if the same day is added more than once.
For example, the following code will raise an exception:
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')
ecx.add_special_open('XLON', date='2022-12-28', name='Special Open', time='11:00')
```
In contrast, removing a day is an idempotent operation, i.e. doing it twice will not raise an exception and keep the 
corresponding changeset the same as after the first removal. 
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()

ecx.remove_day('XLON', date='2022-12-27')
ecx.remove_day('XLON', date='2022-12-27')
```

### Reverting changes

It is sometimes necessary to revert individual changes made to a calendar. To that end the package provides the method 
`reset_day(...)`:

```python
import exchange_calendars_extensions as ecx
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

To reset an entire calendar to its original state, use the method `reset_calendar(...)` or update the calendar with an 
empty ChangeSet:
```python
import exchange_calendars_extensions as ecx
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

### Retrieving changes
For any calendar, it is possible to retrieve a copy of the associated changeset:
```python
import exchange_calendars_extensions as ecx
ecx.apply_extensions()

ecx.add_holiday('XLON', date='2022-12-28', name='Holiday')
ecx.remove_day('XLON', date='2022-12-27')

changeset: ecx.ChangeSet = ecx.get_changes_for_calendar('XLON')
print(changeset)
```
Output:
```
add=[DaySpec(date=Timestamp('2022-12-28 00:00:00'), name='Holiday', type=<DayType.HOLIDAY: 'holiday'>)] remove=[Timestamp('2022-12-27 00:00:00')]
```

Since `ecx.get_changes_for_calendar(...)` returns a copy of the changeset, any modifications to the returned changeset
will not affect the calendar.

To get the changesets for all calendars, use `ecx.get_changes_for_all_calendars()`. This returns a dictionary that 
mapping the exchange name/key to a copy of the corresponding changeset. 

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
sub-module `exchange_calendars_extensions.holiday_calendar`.

```python
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars_extensions import extend_class

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
