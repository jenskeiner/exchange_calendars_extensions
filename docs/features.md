---
title: "Features"
draft: false
type: docs
layout: "single"

menu:
  docs_extensions:
      weight: 10
---
# Features

## Consolidated Calendars

This package adds consolidated calendars for holidays and special open/close days, respectively. These calendars combine 
regular with ad-hoc occurrences. This makes it easier to enumerate these days in order.

{{% note %}}
Depending on the exchange, the consolidated calendars for special open/close days may aggregate days with different 
open/close times into a single calendar. It is currently not possible to recover the open/close time for a day from a 
consolidated calendar.
{{% /note %}}

## Additional Calendars

This package also adds calendars for some special trading sessions and non-trading days of interest:
- the last trading session of the month
- the last regular trading session of the month
- quarterly expiry days (quadruple witching)
- monthly expiry days (in months without a quarterly expiry day)
- weekend days as per the underlying weekmask

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

## Calendar Modifications
It is also possible to modify existing calendars at runtime. This can be used to add or remove
- holidays (regular and ad-hoc)
- special open days (regular and ad-hoc)
- special close days (regular and ad-hoc)
- quarterly expiry days
- monthly expiry days

This may be useful to fix incorrect information from `exchange-calendars`. This regularly happens, e.g., when an 
exchange announces a change to the regular trading schedule on short notice and an updated release of the upstream 
package is not yet available. After some time, modifications can typically be removed when the upstream package has
been updated.

{{% warning %}}
If you find incorrect information, consider opening a pull request on GitHub to update the information directly 
in the [`exchange-calendars`](https://github.com/gerrymanoim/exchange_calendars) repository. Ad-hoc modifications to 
calendars should only be used as a last resort and to bridge the time until the information has been updated at the 
root.
{{% /warning %}}

## Metadata
In some situations, it may be useful to be able to associate arbitrary metadata with certain dates. Here, metadata can 
be a set of string tags and/or a string comment.

{{% note %}}
For example, a tag could be used to mark days on which the exchange 
deviated from the regular trading schedule in an unplanned way, e.g. a delayed open due to technical issues. That is, 
tags or a comment could be useful to incorporate additional user-owned information that would normally be outside the 
scope of the exchange calendars core functionality.
{{% /note %}}

This package provides functionality to add metadata in the form of tags and/or comments to any date in any calendar.
It is then possible to filter dates by their metadata to retrieve only dates within a certain time period that e.g. 
have a certain tag set.
