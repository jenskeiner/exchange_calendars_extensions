# A type alias for pd.Timestamp that allows initialization from suitably formatted string values.
import datetime as dt
from typing import TYPE_CHECKING

import pandas as pd
from pydantic_core import core_schema


class TimestampLike(pd.Timestamp):
    """A pd.Timestamp subtype with Pydantic support."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, v):
        if isinstance(v, cls):
            return v
        if isinstance(v, pd.Timestamp):
            return cls(v)
        try:
            r = cls(v)
            if pd.isna(r):
                raise ValueError()
            return r
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert {v!r} to valid timestamp") from e


# A type alias for TimestampLike that normalizes the timestamp to a date-like value.
#
# Date-like means that the timestamp is timezone-naive and normalized to the date boundary, i.e. midnight of the day it
# represents. If the input converts to a valid pd.Timestamp, any timezone information, if present, is discarded. If the
# result is not aligned with a date boundary, it is normalized to midnight of the same day.
class DateLike(TimestampLike):
    """
    A pd.Timestamp subtype representing a date (timezone-naive, normalized to midnight).

    This type automatically:
    - Converts inputs to a timestamp
    - Removes timezone information
    - Normalizes to midnight of the same day

    Example:
        d = Date("2020-01-01T15:30:00+02:00")
        str(d)  # "2020-01-01 00:00:00"
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_plain_validator_function(
            cls._validate,  # Single source of truth
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, v):
        """Validate and convert to a normalized Date."""
        if isinstance(v, cls):
            return v
        # Reuse Timestamp validation then normalize
        ts = TimestampLike._validate(v)
        return cls(ts.tz_localize(None).normalize())


# A type alias for dt.time that allows initialization from suitably formatted string values.
class TimeLike(dt.time):
    """
    A dt.time subtype with Pydantic support for string conversion.

    Automatically converts from string formats:
    - "%H:%M" (e.g., "09:00")
    - "%H:%M:%S" (e.g., "09:00:00")

    Example:
        t = Time("09:30")
        t.hour    # 9
        t.minute  # 30
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, v):
        """Validate and convert to a Time."""
        if isinstance(v, cls):
            return v
        if isinstance(v, dt.time):
            return cls(v.hour, v.minute, v.second, v.microsecond, v.tzinfo)

        # Try to parse from string
        if isinstance(v, str):
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    parsed = dt.datetime.strptime(v, fmt)
                    return cls(parsed.hour, parsed.minute, parsed.second)
                except ValueError:
                    pass

        raise ValueError(
            f"Cannot convert {v!r} to Time. Expected format 'HH:MM' or 'HH:MM:SS'."
        )


if TYPE_CHECKING:
    DateLikeInput = DateLike | str | pd.Timestamp
    TimestampLikeInput = TimestampLike | str | pd.Timestamp
    TimeLikeInput = TimeLike | str | dt.time
else:
    DateLikeInput = DateLike | str
    TimestampLikeInput = TimestampLike | str
    TimeLikeInput = TimeLike | str
