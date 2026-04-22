---
icon: lucide/cog
---

# Advanced usage

## Adding an extended calendar for a new exchange

The helper function `extend_class` (in `exchange_calendars_extensions.holiday_calendar`) creates an extended calendar
class from any existing exchange calendar class:

```python
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars_extensions import extend_class

xlon_extended_cls = extend_class(XLONExchangeCalendar, day_of_week_expiry=4)
```

- The first argument is the base exchange calendar class to extend.
- `day_of_week_expiry` (optional, defaults to `None`) is the weekday on which expiry days are normally observed
  (Monday = 0 … Friday = 4). When set to `None`, the exchange is assumed not to support monthly or quarterly expiry
  days and the corresponding calendars will not be added.

The returned class inherits directly from the base class and adds the extended attributes (`holidays_all`,
`quarterly_expiries`, etc.). It also supports runtime modifications via `change_day(...)`.

### Registering a new extension

To register a new extended class before activating extensions, use `register_extension()`:

```python
from exchange_calendars_extensions import register_extension, apply_extensions

register_extension("XLON", day_of_week_expiry=4)
apply_extensions()
...
```

The `key` should be the canonical exchange name (not an alias) under which the calendar is registered with the
`exchange_calendars` package.

## Merging holiday calendars

The [exchange-calendars](https://pypi.org/project/exchange-calendars/) package uses
`exchange_calendars.exchange_calendar.HolidayCalendar`, a subclass of
`pandas.tseries.holiday.AbstractHolidayCalendar`. One of its assumptions is that each holiday rule has a **unique
name**. When two calendars are merged via `.merge()`, only one rule per name is kept.

This creates a problem for the aggregate calendars in this package. For example, `holidays_all` must include every
ad-hoc holiday, but ad-hoc holidays have no unique name — they all share the placeholder `ad-hoc holiday`. The
built-in merge would therefore discard all but one of them.

To work around this, the package provides:

```python
from exchange_calendars_extensions import merge_calendars

merged = merge_calendars([calendar_a, calendar_b, ...])
```

`merge_calendars(calendars)` concatenates all rules from the given calendars in order and returns a new
`HolidayCalendar` subclass that filters out duplicate dates when `holidays()` is called.

!!! warning "Always use `merge_calendars(...)` instead of `AbstractHolidayCalendar.merge(...)`"
When merging involves any calendar added by this package, the built-in merge may silently drop ad-hoc holidays.
Use `merge_calendars(...)` to avoid this. Rules earlier in the list take priority when duplicates are encountered.
