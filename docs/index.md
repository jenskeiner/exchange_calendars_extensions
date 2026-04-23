---
icon: lucide/house
---

# exchange-calendars-extensions

A Python package that transparently extends the [exchange-calendars](https://pypi.org/project/exchange-calendars/)
package with additional features.

## Features

Adds the following features to exchange calendars.

**All exchanges:**

- Aggregate calendars that combine *regular* and *ad-hoc* holidays, special open days, and special close days into
  a single calendar, respectively.
- Calendars for the *last* and *last regular* trading session of each month.
- Calendars for weekend and week days.
- API for runtime modifications to any exchange calendar.
- Attach and query arbitrary tags to days.

**Select exchanges:**

- Calendars for monthly and quarterly expiry days (quadruple witching); see [supported exchanges](exchanges.md).

## Installation

The package is available on [PyPI](https://pypi.org/project/exchange-calendars-extensions/) and can be installed
via [uv](https://astral.sh/uv), [pip](https://pip.pypa.io/en/stable/), [Poetry](https://python-poetry.org/), or any
other Python dependency manager.

=== "uv"

    ```bash
    uv add exchange-calendars-extensions
    ```

=== "pip"

    ```bash
    pip install exchange-calendars-extensions
    ```

=== "poetry"

    ```bash
    poetry add exchange-calendars-extensions
    ```

## Quick start

!!! tip

    All code examples in this documentation are self-contained and can be executed in a fresh Python interpreter.

### Adding extensions

To apply the extensions, import `exchange_calendars_extensions` and register the extended calendar classes:

```python
import exchange_calendars_extensions as ecx

ecx.apply_extensions()  # (1)!
```

1. You only need to run this once per session.

This replaces the default classes with their extended versions.

Obtain an exchange calendar instance and verify that it is the extended version.

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

ecx.apply_extensions()

calendar = ec.get_calendar("XLON")

# Still a regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# But also an extended exchange calendar…
assert isinstance(calendar, ecx.ExtendedExchangeCalendar)

# …that implements the extended protocol.
assert isinstance(calendar, ecx.ExchangeCalendarExtensions)
```

Extended calendars are subclasses of `ecx.ExtendedExchangeCalendar`, which inherits from both `ec.ExchangeCalendar` and
the protocol class `ecx.ExchangeCalendarExtensions`.

You can now use extended calendars.

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

### Removing extensions

The original, unextended classes can be restored at any time:

```python
import exchange_calendars as ec
import exchange_calendars_extensions as ecx

ecx.apply_extensions()

...

ecx.remove_extensions()

calendar = ec.get_calendar("XLON")

# A regular exchange calendar.
assert isinstance(calendar, ec.ExchangeCalendar)

# No longer an extended calendar.
assert not isinstance(calendar, ecx.ExtendedExchangeCalendar)
assert not isinstance(calendar, ecx.ExchangeCalendarExtensions)
```

!!! note

    After applying or removing the extensions, exchange calendars must be re-created via `#!python ec.get_calendar()`
    for the changes to be visible. Previously created instances retain their properties.

## What's next?

<div class="grid cards" markdown>

- :lucide-watch: **[Dates & Times](datetime.md)** — Specify dates and times conveniently.
- :lucide-calendar-plus: **[Extended properties](properties.md)** — Aggregate calendars, expiry days, last trading
  days, and more.
- :lucide-square-pen: **[Calendar changes](changes.md)** — Modify any day at runtime: add holidays, change open/close
  times, and more.
- :lucide-box: **[Changesets](changesets.md)** — Apply, inspect, and serialise bulk modifications.
- :lucide-tags: **[Tags](tags.md)** — Attach and query arbitrary labels on days.
- :lucide-landmark: **[Supported exchanges](exchanges.md)** — Exchanges with monthly/quarterly expiry support.
- :lucide-cog: **[Advanced usage](advanced.md)** — Extend new exchanges and merge holiday calendars safely.

</div>
