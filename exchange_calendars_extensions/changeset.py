import datetime as dt
from copy import deepcopy
from enum import Enum, unique
from typing import Set, Generic, TypeVar, Dict, Union, Optional, Any

import pandas as pd
from pydantic import BaseModel, Field, model_validator, ValidationInfo
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Self, Annotated


class DaySpec(BaseModel, extra='forbid'):
    """
    A model for a simple special day specification, for example, holidays.
    """
    name: str  # The name of the special day.


def _validate_time(value):
    if not isinstance(value, dt.time):
        try:
            value = dt.datetime.strptime(value, '%H:%M').time()
        except ValueError:
            try:
                value = dt.datetime.strptime(value, '%H:%M:%S').time()
            except ValueError:
                raise ValueError(f'Failed to convert {value} to {dt.time}.')

    return value


Time = Annotated[dt.time, BeforeValidator(_validate_time)]


class DayWithTimeSpec(BaseModel, extra='forbid'):
    """
    A model for a special day specification that includes a time, for example, special opens.
    """
    name: str  # The name of the special day.
    time: Time  # The open/close time of the special day.


DaySpecT = TypeVar('T')


def _validate_timestamp(value: Any) -> pd.Timestamp:
    # Check if value is a valid timestamp.
    if not isinstance(value, pd.Timestamp):
        try:
            # Convert value to timestamp.
            value = pd.Timestamp(value)
        except ValueError as e:
            # Failed to convert key to timestamp.
            raise ValueError(f'Failed to convert {value} to {pd.Timestamp}.') from e
    return value


Timestamp = Annotated[pd.Timestamp, BeforeValidator(_validate_timestamp)]


class Changes(BaseModel, Generic[DaySpecT], extra='forbid', arbitrary_types_allowed=True, validate_assignment=True):
    """
    Generic internal class to represent a set of calendar changes for a specific day type.

    Changes consist of a set of dates to remove and a dictionary of dates to add. The type parameter T specifies the
    properties to hold for the dates to add. For example, for a holiday calendar, T would be a type containing
    just the name of the holiday. For special open/close days, T would be a type containing the name of the respective
    special day and the associated open/close time.
    """
    add: Dict[Timestamp, DaySpecT] = Field(default=dict())  # The dictionary of dates to add.
    remove: Set[Timestamp] = Field(default=set())  # The set of dates to remove.

    @model_validator(mode='after')
    def _validate_consistency(cls, info: ValidationInfo) -> Any:
        # Check if there are any dates that are both added and removed.
        duplicates = info.add.keys() & info.remove

        if duplicates:
            raise ValueError(f'Inconsistent changes: Dates {", ".join([d.date().isoformat() for d in duplicates])} are both added and removed.')

        return info

    def add_day(self, date: Timestamp, value: Union[DaySpecT, dict]) -> Self:
        """
        Add a date to the set of dates to add.

        If strict is True, raise ValueError if the given date is already in the set of days to remove. If strict is
        False, gracefully remove the date from the set of days to remove, if required, and then add it to the days to
        add. Effectively, setting strict to True raises an Exception before any inconsistent changes are made while
        setting strict to False enforces consistency by removing the date from the set of days to remove before adding.

        Adding the same day twice will overwrite the previous value without raising an exception.

        Parameters
        ----------
        date : Any
            The date to add. Must be convertible to pandas.Timestamp.
        value : T
            The value to add.

        Returns
        -------
        Changes : self

        Raises
        ------
        ValidationError
            If value is not of the expected type or adding date would make the changes inconsistent.
        """
        # Validate date.
        date = Timestamp(date)

        # Save previous value for key. Note that an existing value cannot be None, so we can use it to indicate absence.
        previous = self.add.get(date, None)

        # Add new key and value.
        self.add[date] = value

        try:
            # Trigger validation.
            self.add = self.add
        except Exception as e:
            if previous is None:
                # Delete new entry.
                del self.add[date]
            else:
                # Restore previous entry.
                self.add[date] = previous

            # Re-raise exception.
            raise e

        return self

    def remove_day(self, date: Timestamp) -> Self:
        """
        Add a date to the set of dates to remove.

        If strict is True, raise ValueError if the given date is already in the set of days to add. If strict is
        False, gracefully remove the date from the set of days to add, if required, and then add it to the days to
        remove. Effectively, setting strict to True raises an Exception before any inconsistent changes are made while
        setting strict to False enforces consistency by removing the date from the set of days to add before removing.

        Removing the same day twice will be a no-op without raising an exception.

        Parameters
        ----------
        date : Any
            The date to remove. Must be convertible to pandas.Timestamp.

        Returns
        -------
        Changes : self

        Raises
        ------
        ValidationError
            If removing date would make the changes inconsistent.
        """
        # Validate date.
        date = Timestamp(date)

        # Add the holiday to the set of holidays to remove.
        self.remove.add(date)

        try:
            # Trigger validation.
            self.remove = self.remove
        except Exception as e:
            # Remove the date from the set again. Since an exception was thrown, the date could not have been in the set
            # in the first place.
            self.remove.remove(date)

            # Re-raise exception.
            raise e

        return self

    def clear_day(self, date: Timestamp) -> Self:
        """
        Reset a date so that it is neither in the set of dates to add nor the set of dates to remove.

        Parameters
        ----------
        date : Any
            The date to remove. Must be convertible to pandas.Timestamp.

        Returns
        -------
        Changes
            Self
        """
        # Validate date.
        date = Timestamp(date)

        # Remove the holiday from the set of holidays to add.

        # Check if holiday to remove is already in the dictionary of holidays to add.
        if self.add.get(date) is not None:
            # Remove element from the dictionary.
            del self.add[date]

        # Remove the holiday from the set of holidays to remove.

        # Check if holiday to add is already in the set of holidays to remove.
        if date in self.remove:
            # Remove the holiday from the set of holidays to remove.
            self.remove.remove(date)

        return self

    def clear(self) -> Self:
        """
        Clear all changes.

        Returns
        -------
        Changes : self
        """
        self.add.clear()
        self.remove.clear()

        return self

    def __len__(self) -> int:
        return len(self.add) + len(self.remove)

    def __bool__(self):
        return len(self) > 0

    def __eq__(self, other) -> bool:
        # Check if other is an instance of Changes.
        if not isinstance(other, Changes):
            return False

        # Check if the dictionaries of dates to add and the sets of dates to remove are both equal.
        return self.add == other.add and self.remove == other.remove


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


class ChangeSet(BaseModel, extra='forbid'):
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
    holiday: Changes[DaySpec] = Changes[DaySpec]()
    special_open: Changes[DayWithTimeSpec] = Changes[DayWithTimeSpec]()
    special_close: Changes[DayWithTimeSpec] = Changes[DayWithTimeSpec]()
    monthly_expiry: Changes[DaySpec] = Changes[DaySpec]()
    quarterly_expiry: Changes[DaySpec] = Changes[DaySpec]()

    @model_validator(mode='after')
    def _validate_consistency(cls, info: ValidationInfo) -> ValidationInfo:
        # Maps each date to add to the corresponding day type(s) it appears in.
        date2day_types = dict()

        for day_type in cls.model_fields.keys():
            c: Changes = info[day_type] if isinstance(info, dict) else getattr(info, day_type)
            dates = c.add.keys()
            for d in dates:
                date2day_types[d] = date2day_types.get(d, set()) | {day_type}

        # Remove all entries from date2day_types that only appear in one day type.
        date2day_types = {k: v for k, v in date2day_types.items() if len(v) > 1}

        # Check if there are any dates that appear in multiple day types.
        if len(date2day_types) > 0:
            raise ValueError(f'Inconsistent changes: Dates {", ".join([d.date().isoformat() for d in date2day_types.keys()])} are each added for more than one day type.')

        return info

    def _validate_day_type(self, day_type: Optional[Union[str, DayType]]) -> Union[str, None]:
        # Convert day type to string if necessary.
        day_type = day_type.value if isinstance(day_type, DayType) else day_type

        # Validate day type.
        if day_type is not None and day_type not in self.__fields__.keys():
            raise ValueError(f'Invalid day type {day_type}. Must be one of {self.__fields__.keys()}.')

        return day_type

    def add_day(self, date: Any, value: Union[DaySpec, DayWithTimeSpec, dict], day_type: Union[str, DayType]) -> Self:
        """
        Add a day to the change set.

        Parameters
        ----------
        date : Any
            The date to add. Must be convertible to pandas.Timestamp.
        value : Any
            The value to add.
        day_type : Union[str, DayType]
            The day type to add.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        day_type = self._validate_day_type(day_type)

        try:
            # Add day to set of changes for day type.
            self.__dict__[day_type].add_day(date, value)
        except Exception as e:
            # Failed to add the day to the set of changes, so the set of changes should be unmodified as a result.
            # Just let the exception bubble up.
            raise e
        else:
            # If we get here, then the day has been added to the set of changes successfully.

            # Trigger validation of the entire changeset.
            try:
                self._validate_consistency(self.__dict__)
            except Exception as e:
                # If the changeset is no longer consistent, then this can only be because the day was already a day to
                # add for another day type before and this call added it to the given day type as well, leading to an
                # invalid second add entry.

                # Restore the state before the call by clearing the day from the given day type.
                self.__dict__[day_type].clear_day(date)

                # Let exception bubble up.
                raise e

        return self

    def remove_day(self, date: Any, day_type: Optional[Union[str, DayType]] = None) -> Self:
        """
        Remove a day from the change set.

        Parameters
        ----------
        date : Any
            The date to add. Must be convertible to pandas.Timestamp.
        day_type : Union[str, DayType]
            The day type to remove.

        Returns
        -------
        ExchangeCalendarChangeSet : self

        Raises
        ------
        ValueError
            If removing the given date would make the changeset inconsistent.
        """
        day_type = self._validate_day_type(day_type)

        # Determine which day types to clear.
        day_types = (day_type,) if day_type is not None else tuple(self.__fields__.keys())

        for k in day_types:
            self.__dict__[k].remove_day(date)

        return self

    def clear_day(self, date: Any, day_type: Optional[Union[str, DayType]] = None) -> Self:
        """
        Clear a day from the change set.

        Parameters
        ----------
        date : Any
            The date to add. Must be convertible to pandas.Timestamp.
        day_type : Optional[Union[str, DayType]]
            The day type to clear. If None, all day types will be cleared.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        day_type = self._validate_day_type(day_type)

        # Determine which day types to clear.
        day_types = (day_type,) if day_type is not None else tuple(self.__fields__.keys())

        for k in day_types:
            # Clear for the given day type.
            self.__dict__[k].clear_day(date)

        return self

    def clear(self) -> Self:
        """
        Clear all changes.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        # Clear all changes for all day types.
        for k in self.__fields__.keys():
            self.__dict__[k].clear()

        return self

    def __len__(self):
        return sum(len(self.__dict__[k]) for k in self.__fields__.keys())

    def __eq__(self, other):
        if not isinstance(other, ChangeSet):
            return False

        return all(self.__dict__[k] == other.__dict__[k] for k in self.__fields__.keys())

    def normalize(self, inplace: bool = False) -> Self:
        """
        Normalize the change set.

        A change set is normalized if
        1) It is consistent.
        2) When applied to an exchange calendar, the resulting calendar is consistent.

        Normalization is performed by adding each day to add (for any day type category) also as a day to remove for all
        other day type categories.

        Parameters
        ----------
        inplace : bool
            If True, normalize the change set in-place. If False, return a normalized copy of the change set.
        """

        # Determine instance to normalize.
        if inplace:
            # This instance.
            cs: ChangeSet = self
        else:
            # A copy of this instance.
            cs: ChangeSet = deepcopy(self)

        for day_type in DayType:
            # Get the dates to add for the day type.
            dates_to_add = cs.__dict__[day_type].add.keys()

            # Loop over all day types.
            for day_type0 in DayType:
                if day_type0 != day_type:
                    # Add the dates to add for day_type to the dates to remove for day_type0.
                    for date in dates_to_add:
                        cs.remove_day(date, day_type0)

        return cs
