# exchange-calendars-extensions
A Python package that transparently adds some features to the [exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) 
package.

For select exchanges:
- Add holiday calendar for regular and ad-hoc holidays combined.
- Add holiday calendar for regular and ad-hoc special open days combined.
- Add holiday calendar for regular and ad-hoc special close days combined.
- Add holiday calendar for weekend days.
- Add holiday calendar for quarterly expiry days (aka quadruple witching).
- Add holiday calendar for monthly expiry days (in month without quarterly expiry). 
- Add holiday calendar for last trading day of the month
- Add holiday calendar for last *regular* trading day of the month.

## Installation

The package is available on [PyPI](https://pypi.org/project/exchange-calendars-extensions/) and can be installed via 
[pip](https://pip.pypa.io/en/stable/) or other suitable dependency management tool like 
[Poetry](https://python-poetry.org/).

```bash
pip install exchange-calendars-extensions
```

## Usage

Import the package.
```python
import exchange_calendars_extensions
```

Register extended exchange calendar classes with the `exchange_calendars` package.
```python
exchange_calendars_extensions.apply_extensions()
```
This will replace the default exchange calendar classes with the extended versions for supported exchanges; see [below](#supported-exchanges).

Get an exchange calendar instance.
```python
from exchange_calendars import get_calendar

calendar = get_calendar('XLON')
```

Extended calendars are subclasses of the abstract base class 
`exchange_calendars_extensions.ExtendedExchangeCalendar` which inherits both from `exchange_calendars.ExchangeCalendar`
and the protocol class `exchange_calendars_extensions.ExchangeCalendarExtensions`.
```python
assert isinstance(calendar, exchange_calendars_extensions.ExtendedExchangeCalendar)
assert isinstance(calendar, exchange_calendars.ExchangeCalendar)
assert isinstance(calendar, exchange_calendars_extensions.ExchangeCalendarExtensions)
```

The extended calendars provide the following additional holiday calendars, all instances of 
`exchange_calendars.exchange_calendar.HolidayCalendar`:
- `holidays_all`: Regular and ad-hoc holidays combined into a single calendar.
- `special_opens_all`: Regular and ad-hoc special open days combined into a single calendar.
- `special_closes_all`: Regular and ad-hoc special close days combined into a single calendar.
- `weekend_days`: All weekend days, as defined by the underlying calendar's weekmask, in a single calendar.
- `quarterly_expiries`: Quarterly expiry days, also known as quadruple witching. Many exchanges observe special business
  days on which market index futures, options futures, stock options and stock futures expire, typically resulting in 
  increased volatility and traded volume. Quadruple witching is typically observed on the third Friday of March, June,
  September and December, although some exchanges observe it on Thursday instead. Also, collisions with holidays or
  special open/close days may result in the quarterly expiry day being rolled backward to an otherwise regular business 
- day.
- `monthly_expiries`: Monthly expiry days. Similar to quarterly expiry days, but for the remaining months of the year.
  Monthly expiries are similar to quarterly expiries, but typically result in less extreme trading patterns and may thus
  be treated separately.
- `last_trading_days_of_months`: Last trading day of each month of the year.
- `last_regular_trading_days_of_months`: Last regular trading day of each month of the year, i.e. not a special 
  open/close or otherwise irregular day.

## Examples
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

## Supported exchanges
This package currently provides extensions for the following subset of exchanges supported by `exchange_calendars`:
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

To facilitate the creation of extended classes, the function `extend_class` is provided in the sub-module 
`exchange_calendars_extensions.holiday_calendar`.
```python
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars_extensions.holiday_calendar import extend_class

xlon_extended_cls = extend_class(XLONExchangeCalendar, day_of_week_expiry=4)
```
The first argument to `extend_class` should be the class of the exchange calendar to be extended. The second parameter 
is the day of the week on which expiry days are normally observed. The returned extended class directly inherits from 
the passed base class, but also adds the additional attributes. 

To register a new extended class for an exchange, use the `register_extension` function before calling `apply_extensions()`.
```python
from exchange_calendars_extensions import register_extension, apply_extensions

register_extension(key, cls)

apply_extensions()

...
```
Here, `key` should be the name, i.e. not an alias, under which the extended class is registered with the 
`exchange_calendars` package, and `cls` should be the extended class.

## Contributing
Contributions are welcome. Please open an issue or submit a pull request on GitHub.
