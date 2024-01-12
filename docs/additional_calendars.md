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
