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

The `meta()` method supports `TimestampLike` start and end arguments which must be either both timezone-naive or 
timezone-aware. Otherwise, a `ValueError` is raised.

The returned dictionary includes all days with metadata that overlap with the period between the start and end 
timestamps. This definition ensures that the result is the expected even in situations where the passed in start and end
timestamps are not aligned to midnight. In the above example, if start were `2022-01-01 06:00:00` and end were 
`2022-01-01 18:00:00`, the result would be the same since the time period that represents the full day `2022-01-01` 
overlaps with the period between start and end.

The start and end timestamps can also be timezone-aware. In this case, the time period that represents a day with 
metadata is always interpreted in the timezone of the corresponding exchange.
