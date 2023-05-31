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
available yet.

## Installation
The package is available on [PyPI](https://pypi.org/project/exchange-calendars-extensions/) and can be installed via 
[pip](https://pip.pypa.io/en/stable/) or any other suitable dependency management tool, e.g. 
[Poetry](https://python-poetry.org/).

```bash
pip install exchange-calendars-extensions
```

## Usage
Import the package.
```python
import exchange_calendars_extensions
```

Register extended exchange calendar classes with the `exchange_calendars` module.
```python
exchange_calendars_extensions.apply_extensions()
```
This will replace the default exchange calendar classes with the extended versions. Note that this action currently 
cannot be undone. A new Python interpreter session is required to revert to the original classes. 

Get an exchange calendar instance.
```python
from exchange_calendars import get_calendar

calendar = get_calendar('XLON')
```

Extended exchange calendars are subclasses of the abstract base class 
`exchange_calendars_extensions.ExtendedExchangeCalendar`. This class inherits both from `exchange_calendars.ExchangeCalendar`
and the new protocol class `exchange_calendars_extensions.ExchangeCalendarExtensions` which defines the extended properties.
```python
assert isinstance(calendar, exchange_calendars_extensions.ExtendedExchangeCalendar)
assert isinstance(calendar, exchange_calendars.ExchangeCalendar)
assert isinstance(calendar, exchange_calendars_extensions.ExchangeCalendarExtensions)
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
calendar = get_calendar('XLON')
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
calendar = get_calendar('XLON')
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
calendar = get_calendar('XLON')
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
Extended exchange calendars provide the methods of the form 
`{add,remove}_{holiday,special_open,special_close,quarterly_expiry,monthly_expiry}(...)`at the package level to add or 
remove certain holidays or special sessions programmatically. For example,

```python
import pandas as pd
from exchange_calendars_extensions import add_holiday

add_holiday('XLON', pd.Timestamp('2021-12-27'), 'Holiday')
```
will add a new holiday named `Holiday` to the calendar for the London Stock Exchange on 27 December 2021. Similarly,
```python
import pandas as pd
from exchange_calendars_extensions import remove_holiday

remove_holiday('XLON', pd.Timestamp('2021-12-27'))
```
will remove the holiday from the calendar again.

Holidays are always added as regular holidays. Removing holidays works for both regular and ad-hoc holidays, regardless
whether the affected days were in the original calendar or had been added programmatically at an earlier stage.

Whenever a calendar has been modified programmatically, the changes are only reflected after obtaining a new exchange 
calendar instance.
```python
# Changes not reflected in existing instances.
...
calendar = get_calendar('XLON')
# Changes reflected in new instance.
...
```

The day types that can be added are holidays, special open/close days, and quarterly/monthly expiries. Adding special 
open/close days requires to specify the open/close time in addition to the date.
```python
import pandas as pd
import datetime as dt
from exchange_calendars_extensions import add_special_open

add_special_open('XLON', pd.Timestamp('2021-12-27'), dt.time(11, 0), 'Special Open')
```

The numeration type `exchange_Calendars_extensions.HolidaysAndSpecialSessions` can be used to add or remove holidays in
a more generic way.
```python
import pandas as pd
import datetime as dt
from exchange_calendars_extensions import add_day, remove_day, HolidaysAndSpecialSessions

add_day('XLON', HolidaysAndSpecialSessions.SPECIAL_OPEN, pd.Timestamp('2021-12-27'), {'name': 'Special Open', 'time': dt.time(11, 0)})
remove_day('XLON', pd.Timestamp('2021-12-27'), HolidaysAndSpecialSessions.SPECIAL_OPEN)
```

When removing a day, the day type is optional.
```python
remove_day('XLON', pd.Timestamp('2021-12-27'))
```
If not given, the day will be removed from all calendars it is present in. This is useful to make sure that a given day
does not mark a holiday or any special session. Note that a day could still be a weekend day and that removing the day 
does not change it into a business day.

Removing a day is always handled gracefully when the day is not already present in the calendar, i.e. this does not 
throw an exception.

### Changesets
When a calendar is modified programmatically, the changes are recorded in a changeset. When a new calendar instance is
obtained, the changeset is applied to the underlying unmodified calendar.

Changesets have a notion of consistency. A changeset is consistent if and only if the following conditions are satisfied:
1) For each day type, the corresponding dates to add and dates to remove do not overlap.
2) For each distinct pair of day types, the dates to add must not overlap.

The first condition ensures that the same day is not added and removed at the same time for the same day type. The 
second condition ensures that the same day is not added for two different day types. Note that marking the same day as
a day to remove is valid for multiple day types at the same time since this it will be a no-op if the day is not already
present in the calendar for a day type.

### Strict mode
Multiple calls to add or remove holidays or special sessions can lead to an inconsistent changeset for a calendar or 
situations where the semantics of each action may not be immediately clear without further specification. For example, 
what should happen if the same day is added as a holiday and then removed?
```python
...
add_holiday('XLON', pd.Timestamp('2021-12-27'), 'Holiday')
remove_holiday('XLON', pd.Timestamp('2021-12-27'))

calendar = get_calendar('XLON')
```
By default, situations are handled gracefully as far as possible. Here, the holiday is first added to the changeset and 
then marked as a day to remove for all day types. This would normally lead to an inconsistent changeset since the same
day would now be marked as a holiday to add as well as a day to remove from the holidays (as well as all other day 
types). To remain consistent, the day is is removed from the holidays to add. Now, the changeset only contains the day
as a day to remove for all day types.

This behaviour may not be desired in all cases which is why the `strict` flag can be set to `True` when adding or 
removing a day. In strict mode, conflicting actions such as the ones above will raise an exception.
```python
...
add_holiday('XLON', pd.Timestamp('2021-12-27'), 'Holiday', strict=True)
remove_holiday('XLON', pd.Timestamp('2021-12-27'), strict=True)
# The second call will raise an exception.
```

Another case to consider is trying to add the same day twice with two different day types.
```python
...
add_holiday('XLON', pd.Timestamp('2021-12-27'), 'Holiday')
add_special_open('XLON', pd.Timestamp('2021-12-27'), dt.time(11, 0), 'Special Open')

calendar = get_calendar('XLON')
```
By default, this will not raise an exception. Instead, the second action will overwrite the first one. The resulting 
calendar will therefore just have the day marked as a special open day. In strict mode, however, this will raise an 
exception.
```python
...
add_holiday('XLON', pd.Timestamp('2021-12-27'), 'Holiday', strict=True)
add_special_open('XLON', pd.Timestamp('2021-12-27'), dt.time(11, 0), 'Special Open', strict=True)
# The second call will raise an exception.
```

Strict mode may be particularly useful when an entire changeset is built up through multiple calls that are all expected
to be compatible with each other.

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
