---
title: "Additional Calendars"
draft: false
type: docs
layout: "single"

menu:
  docs_extensions:
      weight: 40
---
# Additional Calendars

Extended exchange calendars provide additional calendars for special trading sessions and non-business days.

## Quarterly Expiry Days

Quarterly expiry days are also known as *triple* or *quadruple witching* days. They represent special trading sessions
when stock index futures, stock index options, stock options and single stock futures expire.

On many exchanges, these sessions take place on the third Friday in March, June, September and December. However, some
exchanges deviate from this pattern. For example, Johannesburg Stock Exchange (XJSE) has quarterly expiry days on the
third Thursday in those months. Also, quarterly expiry days are currently only supported for a limited number of
exchanges.

{{% note title="Supported exchanges for expiry day sessions" collapsible="true" %}}
Calendars for expiry day sessions are currently only available for the following exchanges:
{{% autocolumns %}}
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
{{% /autocolumns %}}
{{% /note %}}

Quarterly expiry trading sessions often differ from regular trading sessions owing to increased volatility and trading
volume. Many exchanges have their own specific rules for these sessions, so some characteristics of these sessions may
be different. For example, the London Stock Exchange (XLON) uses an additional *Exchange Delivery Settlement Price
(EDSP)* auction to determine the reference price for the settlement of derivatives contracts. Other exchanges may use
regular scheduled opening or closing auctions for the same purpose.

{{% note %}}
Modelling the precise characteristics of quarterly expiry trading sessions, beyond providing a calendar, is beyond the
scope of `exchange-calendars-extensions`.
{{% /note %}}

Here is an example for the quarterly expiry days of the London Stock Exchange (XLON):
```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XLON')
print(calendar.quarterly_expiries.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
```
This gives the following output:
```text
2023-03-17    quarterly expiry
2023-06-16    quarterly expiry
2023-09-15    quarterly expiry
2023-12-15    quarterly expiry
dtype: object
```

## Monthly Expiry Days

Similarly to quarterly expiry days, one can observe monthly expiry days during the remaining months. They are likewise
special trading sessions when certain derivatives expire, but typically with less volume and volatility than quarterly
expiry days. They are supported for the same subset of exchanges as quarterly expiry days.

```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XLON')
print(calendar.monthly_expiries.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
```
gives the following output:
```text
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

## Last trading day of the month

It may be of interest to observe the last trading day of any month. While these trading sessions are often not special
per se, they may be interesting nevertheless due to effects around the end of the month. For example, some funds may
re-balance their portfolios at the end of the month, which may lead to increased trading volume and volatility.

```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XLON')
print(calendar.last_trading_days_of_months.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
```
gives the following output:
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
```

{{% note %}}
The last trading day of any month is defined as the last day that the exchange is open in the respective month. This may
sometimes overlap with special trading sessions. For example, the last trading session in December may be a half day on
some exchanges, e.g. XLON. For the last regular trading session of the month, consider
`last_regular_trading_days_of_months` instead.
{{% /note %}}

## Last regular trading day of the month

The last regular trading day of the month is the last trading day of the month that is not a special trading session.
In many cases, the last regular trading day of a month will also be the last trading day of the month, but overlaps with
special sessions, such as half days, are possible.

```python
import exchange_calendars_extensions.core as ecx
import exchange_calendars as ec

ecx.apply_extensions()

calendar = ec.get_calendar('XLON')
print(calendar.last_regular_trading_days_of_months.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
print(calendar.special_closes_all.holidays(start='2023-12-29', end='2023-12-31', return_name=True))
```
gives the following output:
```text
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
2023-12-29    New Year's Eve
dtype: object
```

Note that the last regular trading day in December is the 28th, not the 29th, as the 29th was a special trading session
(New Year's Eve) on XLON.

## Conflicts with other special days
Special sessions like expiry days or the last trading day of the month typically need to be adjusted for holidays or
early open/close days that may occur on the original provisioned dates. The exact rules for these adjustments are
exchange-specific, can be difficult to find in writing, and may also change over time.

In most cases, rolling back to the previous trading day is the correct approach. Currently, quarterly/monthly expiries
and the last (regular) trading days of the month are rolled back to the previous day until all conflicts with other
special days are resolved.

{{% note %}}
The current conflict resolution rules seem to be correct for most exchanges. However, there may be exceptions. If you
find any, please open an issue on GitHub, ideally with a link to the exchange's official documentation.
{{% /note %}}

Quarterly/monthly expiries and the last regular trading days of the month adjust for holidays and special open/close
days. In contrast, the last trading days of the month do *not* adjust for special open/close days, but only for
holidays.



{{% note %}}
The current conflict resolution rules do not allow a day to be rolled back over a month boundary. In a scenario where
this would otherwise occur, the special session in question is just dropped. This is because the definition of expiry
days as well as last trading days of the month does not make sense when rolled back over a month boundary.

This case may seem like a theoretical scenario, but it has occurred in the past. For example,
ASEX was closed on all days in July 2015. Therefore, the last trading day of July 2015 would roll back to the last
trading day of June 2015. This obviously does not make sense, so this special session is dropped from the calendar.
{{% /note %}}
