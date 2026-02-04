---
title: "Metadata"
draft: false
type: docs
layout: "single"

menu:
  docs_extensions:
      weight: 60
---
# Metadata

Metadata in the form of tags and comments can be associated with specific dates. Metadata can be a combination of a
single string comment and/or a set of string tags. For example,
```python
import pandas as pd

import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

# Add metadata.
ecx.set_comment('XLON', '2022-01-01', "This is a comment.")
ecx.set_tags('XLON', '2022-01-01', {'tag1', 'tag2'})

calendar = ec.get_calendar('XLON')

# Get metadata.
meta_dict = calendar.meta()
print(len(meta_dict))

# The value for the first and only date.
meta = meta_dict[pd.Timestamp('2022-01-01')]

print(meta.comment)
print(meta.tags)
```
will print
```text
1
This is a comment.
{'tag1', 'tag2'}
```

The `meta()` method returns an ordered dictionary of type `Dict[pd.Timestamp, DayMeta]` that contains all days that have
metadata associated with them, ordered by date. The keys are `DateLike` timezone-naive Pandas timestamps normalized to
midnight. Each timestamp represents a full day starting at midnight (inclusive) and ending at midnight (exclusive) of
the following day within the relevant timezone for the exchange.


{{% note %}}
Currently, the dictionary returned by the `meta()` method does not support lookup from values other than
`pandas.Timestamp`. This means that it is not possible to look up metadata for a specific date using a string.
{{% /note %}}

Dates can be filtered by a start and an end timestamp. For example,
```python
import pandas as pd

import exchange_calendars_extensions.core as ecx
ecx.apply_extensions()
import exchange_calendars as ec

# Add metadata for two dates.
ecx.set_comment('XLON', '2022-01-01', "This is a comment.")
ecx.set_tags('XLON', '2022-01-01', {'tag1', 'tag2'})
ecx.set_comment('XLON', '2022-01-02', "This is another comment.")
ecx.set_tags('XLON', '2022-01-02', {'tag3', 'tag4'})

calendar = ec.get_calendar('XLON')

# Get metadata only for 2022-01-01.
meta_dict = calendar.meta(start='2022-01-01', end='2022-01-01')
print(len(meta_dict))

# The value for the first and only date.
meta = meta_dict[pd.Timestamp('2022-01-01')]

print(meta.comment)
print(meta.tags)
```
will print
```text
1
This is a comment.
{'tag1', 'tag2'}
```

The `meta()` method supports `TimestampLike` `start` and `end` arguments which must be either both timezone-naive or
timezone-aware. Otherwise, a `ValueError` is raised.

The returned dictionary includes all days with metadata that have a non-empty intersection with the period between
the `start` and `end`. This result is probably what one would usually expect, even in situations where `start` and/or
`end` are not aligned to midnight. In the above example, if `start` were `2022-01-01 06:00:00` and `end` were
`2022-01-01 18:00:00`, the result would be the same since the intersection with the full day `2022-01-01` is non-empty.

When `start` and `end` are timezone-naive, as in the examples above, the timezone of the exchange does not matter. Like
`start` and `end`, the timestamps that mark the beginning and end of a day are used timezone-naive. Effectively, any
comparison uses timestamps with a wall-clock time component.

In contrast, when `start` and `end` timestamps are timezone-aware, all other timestamps also used timezone-aware and
with the exchange's native timezone. Comparisons are then done between instants, i.e. actual points on the timeline.

The difference between the two cases is illustrated in the following example which considers the date 2024-03-31. In
timezones that are based on Central European Time (CET), a transition to Central European Summer Time (CEST) occurs on
this date. The transition happens at 02:00:00 CET, which is 03:00:00 CEST, i.e. clocks advance by one hour and the day
is 23 hours long.
```python
import pandas as pd

import exchange_calendars_extensions.core as ecx
from collections import OrderedDict
from exchange_calendars_extensions.api.changes import DayMeta
ecx.apply_extensions()
import exchange_calendars as ec

# Add metadata.
day = pd.Timestamp("2024-03-31")
meta = DayMeta(tags=[], comment="This is a comment")
ecx.set_meta('XETR', day, meta)

calendar = ec.get_calendar('XETR')

# Get metadata for 2024-03-31, timezone-naive.
assert calendar.meta(start='2024-03-31 00:00:00') == OrderedDict([(day, meta)])
assert calendar.meta(start='2024-03-31 23:59:59') == OrderedDict([(day, meta)])

# Get metadata for 2024-03-31, timezone-aware.
# 2024-03-30 23:00:00 UTC is 2024-03-31 00:00:00 CET.
assert calendar.meta(start=pd.Timestamp('2024-03-30 23:00:00').tz_localize("UTC")) == OrderedDict([(day, meta)])
# 2024-03-31 21:59:59 UTC is 2024-03-31 23:59:59 CEST.
assert calendar.meta(start=pd.Timestamp('2024-03-31 21:59:59').tz_localize("UTC")) == OrderedDict([(day, meta)])
# 2024-03-31 22:00:00 UTC is 2024-03-31 00:00:00 CEST.
assert calendar.meta(start=pd.Timestamp('2024-03-31 22:00:00').tz_localize("UTC")) == OrderedDict([])
```
