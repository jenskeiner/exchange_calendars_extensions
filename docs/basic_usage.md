---
title: "Basic Usage"
draft: false
type: docs
layout: "single"

menu:
  docs_extensions:
      weight: 20
---
# Basic Usage
To use the extensions, import the top-level module and register the extended exchange calendar classes.
```python
import exchange_calendars_extensions.core as ecx

# Apply extensions.
ecx.apply_extensions()
```
This replaces the default calendar classes in `exchange_calendars` with the extended versions. You can now use these
extended classes while existing code should continue to work as before.

## Extended Exchange Calendars

```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

# Get an exchange calendar instance.
calendar = ec.get_calendar('XLON')

# It's still a regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# But it's also an extended exchange calendar...
assert isinstance(calendar, ecx.ExtendedExchangeCalendar)

# ...that implements a protocol that defines additional properties.
assert isinstance(calendar, ecx.ExchangeCalendarExtensions)
```

{{% note %}}
The class `ecx.ExtendedExchangeCalendar` is an abstract base class that inherits from `ec.ExchangeCalendar` and the 
protocol class `ecx.ExchangeCalendarExtensions` which defines the extended properties.
{{% /note %}}


## Removing Extensions

In the unlikely case that you later need to re-instate the original classes, you can do so:

```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

...

ecx.remove_extensions()

calendar = ec.get_calendar('XLON')

# It's a regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# But it's not an extended exchange calendar anymore.
assert not isinstance(calendar, ecx.ExtendedExchangeCalendar)
assert not isinstance(calendar, ecx.ExchangeCalendarExtensions)
```
