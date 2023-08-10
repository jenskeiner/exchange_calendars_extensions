import datetime as dt
from enum import Enum, unique
from functools import reduce
from typing import Union, List, Tuple

import pandas as pd
from pydantic import BaseModel, Field, model_validator, validate_call
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Self, Annotated, Literal


@unique
class DayType(str, Enum):
    """
    Enum for the different types of holidays and special sessions.

    HOLIDAY: A holiday.
    SPECIAL_OPEN: A special session with a special opening time.
    SPECIAL_CLOSE: A special session with a special closing time.
    MONTHLY_EXPIRY: A monthly expiry.
    QUARTERLY_EXPIRY: A quarterly expiry.
    """
    HOLIDAY = 'holiday'
    SPECIAL_OPEN = 'special_open'
    SPECIAL_CLOSE = 'special_close'
    MONTHLY_EXPIRY = 'monthly_expiry'
    QUARTERLY_EXPIRY = 'quarterly_expiry'


def _to_timestamp(value: Union[pd.Timestamp, str]) -> pd.Timestamp:
    """
    Convert value to Pandas timestamp.

    Parameters
    ----------
    value : Union[pd.Timestamp, str]
        The value to convert.

    Returns
    -------
    pd.Timestamp
        The converted value.

    Raises
    ------
    ValueError
        If the value cannot be converted to pd.Timestamp.
    """
    # Check if value is a valid timestamp.
    if not isinstance(value, pd.Timestamp):
        try:
            # Convert value to timestamp.
            value = pd.Timestamp(value)
        except ValueError as e:
            # Failed to convert key to timestamp.
            raise ValueError(f'Failed to convert {value} to {pd.Timestamp}.') from e
    return value


# A type alias for pd.Timestamp that allows initialisation from suitably formatted string values.
TimestampLike = Annotated[pd.Timestamp, BeforeValidator(_to_timestamp)]


class AbstractDaySpec(BaseModel, arbitrary_types_allowed=True, validate_assignment=True, extra='forbid'):
    """
    Abstract base class for special day specification.
    """
    date: TimestampLike  # The date of the special day.
    name: str  # The name of the special day.


class DaySpec(AbstractDaySpec):
    """
    Vanilla special day specification.
    """
    type: Literal[DayType.HOLIDAY, DayType.MONTHLY_EXPIRY, DayType.QUARTERLY_EXPIRY]  # The type of the special day.

    def __str__(self):
        return f'{{date={self.date.date().isoformat()}, type={self.type.name}, name="{self.name}"}}'


def _to_time(value: Union[dt.time, str]):
    """
    Convert value to time.

    Parameters
    ----------
    value : Union[dt.time, str]
        The value to convert.

    Returns
    -------
    dt.time
        The converted value.

    Raises
    ------
    ValueError
        If the value cannot be converted to dt.time.
    """
    if not isinstance(value, dt.time):
        for f in ('%H:%M', '%H:%M:%S'):
            try:
                value = dt.datetime.strptime(value, f).time()
                break
            except ValueError:
                pass

        if not isinstance(value, dt.time):
            raise ValueError(f'Failed to convert {value} to {dt.time}.')

    return value


# A type alias for dt.time that allows initialisation from suitably formatted string values.
TimeLike = Annotated[dt.time, BeforeValidator(_to_time)]


class DaySpecWithTime(AbstractDaySpec):
    """
    Special day specification that requires a (open/close) time.
    """
    type: Literal[DayType.SPECIAL_OPEN, DayType.SPECIAL_CLOSE]  # The type of the special day.
    time: TimeLike  # The open/close time of the special day.

    def __str__(self):
        return f'{{date={self.date.date().isoformat()}, type={self.type.name}, name="{self.name}", time={self.time}}}'


class ChangeSet(BaseModel, arbitrary_types_allowed=True, validate_assignment=True, extra='forbid'):
    """
    Represents a modification to an existing exchange calendar.

    A changeset consists of a set of dates to add and a set of dates to remove, respectively, for each of the following
    types of days:
    - holidays
    - special open
    - special close
    - monthly expiry
    - quarterly expiry

    A changeset is consistent if and only if the following conditions are satisfied:
    1) For each day type, the corresponding dates to add and dates to remove do not overlap.
    2) For each distinct pair of day types, the dates to add must not overlap

    Condition 1) ensures that the same day is not added and removed at the same time for the same day type. Condition 2)
    ensures that the same day is not added for two different day types.

    Consistency does not require a condition similar to 2) for dates to remove. This is because removing a day from a
    calendar can never make it inconsistent. For example, if a changeset contains the same day as a day to remove for
    two different day types, then applying these changes to a calendar will result in the day being removed from the
    calendar at most once (if it was indeed a holiday or special day in the original calendar) or not at all otherwise.
    Therefore, changesets may specify the same day to be removed for multiple day types, just not for day types that
    also add the same date.

    A changeset is normalized if and only if the following conditions are satisfied:
    1) It is consistent.
    2) When applied to an exchange calendar, the resulting calendar is consistent.

    A changeset that is consistent can still cause an exchange calendar to become inconsistent when applied. This is
    because consistency of a changeset requires the days to be added to be mutually exclusive only across all day types
    within the changeset. However, there may be conflicting holidays or special days already present in a given exchange
    calendar to which a changeset is applied. For example, assume the date 2020-01-01 is a holiday in the original
    calendar. Then, a changeset that adds 2020-01-01 as a special open day will cause the resulting calendar to be
    inconsistent. This is because the same day is now both a holiday and a special open day.

    To resolve this issue, the date 2020-01-01 could be added to the changeset, respectively, for all day types (except
    special opens) as a day to remove. Now, if the changeset is applied to the original calendar, 2020-01-01 will no
    longer be a holiday and therefore no longer conflict with the new special open day. This form of sanitization
    ensures that a consistent changeset can be applied safely to any exchange calendar. Effectively, normalization
    ensures that adding a new day for a given day type becomes an upsert operation, i.e. the day is added if it does not
    already exist in any day type category, and updated/moved to the new day type if it does.
    """
    add: List[Annotated[Union[DaySpec, DaySpecWithTime], Field(discriminator='type')]] = Field(default_factory=list)
    remove: List[TimestampLike] = Field(default_factory=list)

    @model_validator(mode='after')
    def _validate_consistency(self) -> 'ChangeSet':
        add = sorted(self.add, key=lambda x: x.date)
        remove = sorted(set(self.remove))

        # Get list of duplicate days to add.
        if len(add) > 0:
            dupes = list(filter(lambda x: len(x) > 1, reduce(lambda x, y: x[:-1] + ([x[-1] + [y]] if x[-1][0].date == y.date else [x[-1], [y]]), add[1:], [[add[0]]])))

            if len(dupes) > 0:
                raise ValueError(f'Duplicates in days to add: {", ".join(("[" + ", ".join(map(str, d)) + "]" for d in dupes))}.')

        self.__dict__['add'] = add
        self.__dict__['remove'] = remove
        return self

    @validate_call(config={'arbitrary_types_allowed': True})
    def add_day(self, spec: Annotated[Union[DaySpec, DaySpecWithTime, dict], Field(discriminator='type')]) -> Self:
        """
        Add a day to the change set.

        Parameters
        ----------
        spec : Annotated[Union[DaySpec, DaySpecWithTime], Field(discriminator='type')]
            The day to add.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        self.add.append(spec)

        # Trigger validation.
        try:
            self.model_validate(self, strict=True)
        except Exception as e:
            # If the days to add are no longer consistent, then this can only be because the date was already in the
            # list. Remove the offending duplicate.
            self.add.remove(spec)

            # Let exception bubble up.
            raise e

        return self

    @validate_call(config={'arbitrary_types_allowed': True})
    def remove_day(self, date: TimestampLike) -> Self:
        """
        Remove a day from the change set.

        Parameters
        ----------
        date : TimestampLike
            The date to remove.

        Returns
        -------
        ExchangeCalendarChangeSet : self

        Raises
        ------
        ValueError
            If removing the given date would make the changeset inconsistent. This can only be if the date is already in
            the days to remove.
        """
        self.remove.append(date)

        try:
            # Trigger validation.
            self.model_validate(self, strict=True)
        except Exception as e:
            self.remove.remove(date)

            # Let exception bubble up.
            raise e

        return self

    @validate_call(config={'arbitrary_types_allowed': True})
    def clear_day(self, date: TimestampLike) -> Self:
        """
        Clear a day from the change set.

        Parameters
        ----------
        date : TimestampLike
            The date to clear. Must be convertible to pandas.Timestamp.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """

        # Avoid re-validation since this change cannot make the changeset inconsistent.
        self.__dict__['add'] = [x for x in self.add if x.date != date]
        self.__dict__['remove'] = [x for x in self.remove if x != date]

        return self

    def clear(self) -> Self:
        """
        Clear all changes.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        self.add.clear()
        self.remove.clear()

        return self

    def __len__(self):
        return len(self.add) + len(self.remove)

    def __eq__(self, other):
        if not isinstance(other, ChangeSet):
            return False

        return self.add == other.add and self.remove == other.remove

    @property
    def all_days(self) -> Tuple[pd.Timestamp]:
        """
        All unique dates contained in the changeset.

        This is the union of the dates to add and the dates to remove, with any duplicates removed.

        Returns
        -------
        Iterable[pd.Timestamp]
            All days in the changeset.
        """
        return tuple(sorted(set(map(lambda x: x.date, self.add)).union(set(self.remove))))
