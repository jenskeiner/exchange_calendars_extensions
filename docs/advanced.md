---
icon: lucide/cog
---

# Advanced usage

## Registering a new calendar

In [exchange-calendars](https://pypi.org/project/exchange-calendars/), you can use `register_calendar()` and
`register_calendar_type()` to register new exchange
calendar instances and types, and `register_calendar_alias()` to make an existing instance/type available under a
different name.

This functionality naturally carries over to when the extensions provided by this package are applied
via `apply_extensions()`.

### Calendar instances

When a plain exchange calendar *instance* is registered, it is not automatically extended. This is because extension
works at the class level to derive extended classes with the additional properties from the plain ones.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

c0 = ec.get_calendar("XLON")  # Plain calendar instance.

assert isinstance(c0, ec.ExchangeCalendar)
assert not isinstance(c0, ecx.ExtendedExchangeCalendar)

ecx.apply_extensions()

# Register the instance under a different name.
ec.register_calendar("TEST", c0)

c = ec.get_calendar("TEST")

# Should be identical to the registered instance.
assert c is c0

ecx.remove_extensions()

c = ec.get_calendar("TEST")

# Should still be identical to the registered instance.
assert c is c0
```

!!! warning

    When calendar instances are registered this way, they do not support runtime modifications, as this requires
    an extended calendar class.

### Calendar classes

When registering a plain exchange calendar *class*, it is automatically extended.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

klass = ec.get_calendar("XLON").__class__  # Plain calendar class.

assert issubclass(klass, ec.ExchangeCalendar)
assert not issubclass(klass, ecx.ExtendedExchangeCalendar)

ecx.apply_extensions()

# Register the class under a different name.
ec.register_calendar_type("TEST", klass)

c = ec.get_calendar("TEST")

assert isinstance(c, ec.ExchangeCalendar)
assert isinstance(c, ecx.ExtendedExchangeCalendar)
assert len(c.quarterly_expiries.rules) == 0  # Should not have quarterly expiries.

ecx.remove_extensions()

c = ec.get_calendar("TEST")

assert isinstance(c, ec.ExchangeCalendar)
assert not isinstance(c, ecx.ExtendedExchangeCalendar)
```

Note that after the call to `remove_extensions()`, the original class is recovered.

### Extension specifications

Most of the extended properties and behaviors of extended exchange calendars are added automatically. However, optional
features like expiry day calendars require additional specification per calendar class. If undefined for an exchange,
these optional features are not added when extending the class.

To register a new specification for optional features, call `register_extension()` before registering a new calendar
class.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

klass = ec.get_calendar("XLON").__class__  # Plain calendar class.

ecx.register_extension("TEST", day_of_week_expiry=4)

ecx.apply_extensions()

# Register the class under a different name.
ec.register_calendar_type("TEST", klass)

c = ec.get_calendar("TEST")

assert isinstance(c, ec.ExchangeCalendar)
assert isinstance(c, ecx.ExtendedExchangeCalendar)
assert len(c.quarterly_expiries.rules) > 0  # Should have quarterly expiries.
```

### Extended calendar classes

It is possible to create an extended calendar class manually. The helper function `extend_class()` creates an extended
calendar class from any existing exchange calendar class. Extended classes can be registered with
`register_calendar_type()` as usual.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar

klass = ecx.extend_class(XLONExchangeCalendar, day_of_week_expiry=4)

ecx.apply_extensions()

ec.register_calendar_type("TEST", klass)

c = ec.get_calendar("TEST")

assert isinstance(c, ec.ExchangeCalendar)
assert isinstance(c, ecx.ExtendedExchangeCalendar)
assert len(c.quarterly_expiries.rules) > 0  # Should have quarterly expiries.
```

!!! note

    Manualy created extended exchange calendar classes support runtime modifications through `change_day()` just as any
    other calendar class *after* registration.

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
