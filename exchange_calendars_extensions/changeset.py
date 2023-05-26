import datetime as dt
import itertools
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Set, Generic, TypeVar, Any, Dict, Self, TypedDict, Union, Optional

import pandas as pd
import schema as s

T = TypeVar('T')


@dataclass
class Changes(Generic[T]):
    """
    Generic internal class to represent a set of changes to a calendar.

    Changes consist of a set of dates to remove and a dictionary of dates to add. The type parameter T is the type of
    the value for dates to add to the calendar. For example, for a holiday calendar, T would be a type containing
    just the name of the holiday, while for special open/close days, T would be a type containing the name of the
    special day and the open/close time.
    """

    @property
    def add(self) -> Dict[pd.Timestamp, T]:
        # Return a read-only view of the dictionary of dates to add.
        return MappingProxyType(self._add)

    @property
    def remove(self) -> Set[pd.Timestamp]:
        # Return a read-only view of the set of dates to remove.
        return frozenset(self._remove)

    def __init__(self, schema: s.Schema) -> None:
        """
        Constructor.

        Parameters
        ----------
        schema : Schema
            The schema to use to validate the values to add.

        Returns
        -------
        None
        """
        # Save schema.
        self._schema = schema
        # Initialize properties.
        self._add = dict()
        self._remove = set()

    def _remove_from_add(self, date: pd.Timestamp) -> None:
        """
        Remove a date from the dictionary of dates to add.

        Gracefully returns directly if the given date is not in the dictionary of dates to add.

        Parameters
        ----------
        date : pd.Timestamp
            The date to remove.

        Returns
        -------
        None
        """
        # Check if holiday to remove is already in the dictionary of holidays to add.
        if self._add.get(date) is not None:
            # Remove element from the dictionary.
            del self._add[date]

    def _remove_from_remove(self, date: pd.Timestamp) -> None:
        """
        Remove a date from the set of dates to remove.

        Gracefully returns directly if the given date is not in the set of dates to remove.

        Parameters
        ----------
        date : pd.Timestamp
            The date to remove.

        Returns
        -------
        None
        """
        # Check if holiday to add is already in the set of holidays to remove.
        if date in self._remove:
            # Remove the holiday from the set of holidays to remove.
            self._remove.remove(date)

    def add_day(self, date: pd.Timestamp, value: T, strict: bool) -> Self:
        """
        Add a date to the set of dates to add.

        If strict is True, raise ValueError if the given date is already in the set of days to remove. If strict is
        False, gracefully remove the date from the set of days to remove, if required, and then add it to the days to
        add. Effectively, setting strict to True raises an Exception before any inconsistent changes are made while
        setting strict to False enforces consistency by removing the date from the set of days to remove before adding.

        Adding the same day twice will overwrite the previous value without raising an exception.

        Parameters
        ----------
        date : pd.Timestamp
            The date to add.
        value : T
            The value to add.
        strict : bool, optional
            If True, raise ValueError if the given date is already in the set of days to remove. If False, gracefully
            remove the date from the set of days to remove, if required, and then add it to the days to add.

        Returns
        -------
        Changes : self

        Raises
        ------
        SchemaError
            If the value does not match the schema.
        ValueError
            If strict is True and the given date is already in the set of days to remove.
        """
        # Validate value against schema.
        value = self._schema.validate(value)

        # Ensure consistency by removing from days to remove, maybe.
        if strict:
            if date in self._remove:
                raise ValueError(f'Date {date} is already in the set of days to remove.')
        else:
            self._remove_from_remove(date)

        # Add the holiday to the set of holidays to add. Also overwrites any previous entry for the date.
        self._add[date] = value

        return self

    def remove_day(self, date: pd.Timestamp, strict: bool) -> Self:
        """
        Add a date to the set of dates to remove.

        If strict is True, raise ValueError if the given date is already in the set of days to add. If strict is
        False, gracefully remove the date from the set of days to add, if required, and then add it to the days to
        remove. Effectively, setting strict to True raises an Exception before any inconsistent changes are made while
        setting strict to False enforces consistency by removing the date from the set of days to add before removing.

        Removing the same day twice will be a no-op without raising an exception.

        Parameters
        ----------
        date : pd.Timestamp
            The date to remove.
        strict : bool, optional
            If True, raise ValueError if the given date is already in the set of days to add. If False, gracefully
            remove the date from the set of days to add, if required, and then add it to the days to remove.

        Returns
        -------
        Changes : self

        Raises
        ------
        ValueError
            If strict is True and the given date is already in the set of days to add.
        """
        # Ensure consistency by removing from days to add, maybe.
        if strict:
            if self._add.get(date) is not None:
                raise ValueError(f'Date {date} is already in the set of days to add.')
        else:
            self._remove_from_add(date)

        # Add the holiday to the set of holidays to remove. Will be a no-op if the date is already in the set.
        self._remove.add(date)

        return self

    def clear_day(self, date: pd.Timestamp) -> Self:
        """
        Reset a date so that it is neither in the set of dates to add nor the set of dates to remove.

        Parameters
        ----------
        date : pd.Timestamp
            The date to reset.

        Returns
        -------
        Changes
            Self
        """
        # Remove the holiday from the set of holidays to add.
        self._remove_from_add(date)

        # Remove the holiday from the set of holidays to remove.
        self._remove_from_remove(date)

        return self

    def clear(self) -> Self:
        """
        Clear all changes.

        Returns
        -------
        Changes : self
        """
        self._add.clear()
        self._remove.clear()

        return self

    def is_consistent(self) -> bool:
        """
        Return whether the changes are consistent.

        Changes are consistent if and only if dates to add and dates to remove do not overlap.

        Returns
        -------
        bool
            True if the changes are consistent, False otherwise.
        """
        # Check if any dates are in both the set of holidays to add and the set of holidays to remove.
        return len(self.add.keys() & self.remove) == 0

    def is_empty(self) -> bool:
        """
        Check if the changes are empty.

        Changes are empty when both the set of dates to add and the set of dates to remove are empty.

        Returns
        -------
        bool
            True if the changes are empty, False otherwise.
        """
        return len(self.add) == 0 and len(self.remove) == 0

    def __eq__(self, other) -> bool:
        # Check if other is an instance of Changes.
        if not isinstance(other, Changes):
            return False

        # Check if the dictionaries of dates to add and the sets of dates to remove are both equal.
        return self.add == other.add and self.remove == other.remove

    def __copy__(self):
        c = Changes()
        c._add = self._add
        c_remove = self._remove
        return c

    def __deepcopy__(self, memo):
        c = Changes(self._schema)
        c._add = deepcopy(self._add, memo)
        c._remove = deepcopy(self._remove, memo)
        return c

    @staticmethod
    def _format_dict(d: Dict[pd.Timestamp, T]) -> str:
        """
        Format a dictionary of dates to values as a string.

        Parameters
        ----------
        d : Dict[pd.Timestamp, T]
            The dictionary to format.

        Returns
        -------
        str
            The formatted string.
        """
        return '{' + ', '.join([f'{k.date().isoformat()}: {v}' for k, v in d.items()]) + '}'

    @staticmethod
    def _format_set(s: Set[pd.Timestamp]) -> str:
        """
        Format a set of dates as a string.

        Parameters
        ----------
        s : Set[pd.Timestamp]
            The set to format.

        Returns
        -------
        str
            The formatted string.
        """
        return '{' + ', '.join([d.date().isoformat() for d in s]) + '}'

    def __str__(self) -> str:
        return f'Changes(add={self._format_dict(self._add)}, remove={self._format_set(self._remove)})'


def _to_time(input: Union[str, dt.time]) -> dt.time:
    """
    Gracefull convert an input value to a datetime.time.

    Parameters
    ----------
    input : Union[str, dt.time]
        The input value to convert.

    Returns
    -------
    dt.time
        The converted value.

    Raises
    ------
    ValueError
        If the input value cannot be converted to a datetime.time.
    """
    if isinstance(input, dt.time):
        return input
    try:
        return dt.datetime.strptime(input, '%H:%M').time()
    except ValueError:
        return dt.datetime.strptime(input, '%H:%M:%S').time()


# Define types and schemas for the different types of holidays and special sessions.
DaySpec = TypedDict('DAY_SPEC', {'name': str})
_DaySchema = s.Schema({'name': str})
DaySpecWithTime = TypedDict('DAY_SPEC_WITH_TIME', {'name': str, 'time': dt.time})
_DayWithTimeSchema = s.Schema({'name': str, 'time': s.Use(_to_time)})


class HolidaysAndSpecialSessions(Enum):
    """
    Enum for the different types of holidays and special sessions.

    HOLIDAY: A holiday.
    SPECIAL_OPEN: A special session with a special opening time.
    SPECIAL_CLOSE: A special session with a special closing time.
    MONTHLY_EXPIRY: A monthly expiry.
    QUARTERLY_EXPIRY: A quarterly expiry.

    Each enum value is a tuple of the following form:
    (id, type, schema)
    where
    id: int
        Unique int to ensure enum value uniqueness.
    type: Type[Union[DaySpec, DaySpecWithTime]]
        Type of the value of the enum value.
    schema: Schema
        Schema for the value of the enum value.
    """
    HOLIDAY = (1, DaySpec, _DaySchema)
    SPECIAL_OPEN = (2, DaySpecWithTime, _DayWithTimeSchema)
    SPECIAL_CLOSE = (3, DaySpecWithTime, _DayWithTimeSchema)
    MONTHLY_EXPIRY = (4, DaySpec, _DaySchema)
    QUARTERLY_EXPIRY = (5, DaySpec, _DaySchema)

    @staticmethod
    def from_str(key: str):
        """
        Return the enum value corresponding to the given key. Case-insensitive.

        Parameters
        ----------
        key : str
            The key to look up.

        Returns
        -------
        HolidaysAndSpecialSessions
            The enum value corresponding to the given key.
        """
        return HolidaysAndSpecialSessions[key.upper()]


# Define a schema for a dictionary to represent a changeset containing changes to an exchange calendar. Note that the
# schema only defines the expected structure, i.e. the keys and the types of the values. It does not validate the values
# themselves. A dictionary that is valid with respect to this schema may still contain an invalid combination of dates.
# For example, it may contain a date that is in the set of dates to add for two different types of days like holidays
# and special open. This is obviously inconsistent as the same day can only be one of those two types of days.
_SCHEMA = s.Schema({
    s.Optional('holiday'): {s.Optional('add'): [{'date': s.Use(pd.Timestamp), 'value': _DaySchema}], s.Optional('remove'): [s.Use(pd.Timestamp)]},
    s.Optional('special_open'): {s.Optional('add'): [{'date': s.Use(pd.Timestamp), 'value': _DayWithTimeSchema}], s.Optional('remove'): [s.Use(pd.Timestamp)]},
    s.Optional('special_close'): {s.Optional('add'): [{'date': s.Use(pd.Timestamp), 'value': _DayWithTimeSchema}], s.Optional('remove'): [s.Use(pd.Timestamp)]},
    s.Optional('monthly_expiry'): {s.Optional('add'): [{'date': s.Use(pd.Timestamp), 'value': _DaySchema}], s.Optional('remove'): [s.Use(pd.Timestamp)]},
    s.Optional('quarterly_expiry'): {s.Optional('add'): [{'date': s.Use(pd.Timestamp), 'value': _DaySchema}], s.Optional('remove'): [s.Use(pd.Timestamp)]},
})


@dataclass
class ChangeSet:
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

    @property
    def changes(self) -> Dict[HolidaysAndSpecialSessions, Changes[Union[DaySpec, DaySpecWithTime]]]:
        """
        The changes.

        Returns
        -------
        Dict[HolidaysAndSpecialSessions, Changes[Any]]
            The changes.
        """
        # Return a read-only view of the _changes dictionary.
        return MappingProxyType(self._changes)

    def __init__(self) -> None:
        """
        Initialize a new instance of ChangeSet.
        """
        # Initialize the _changes dictionary.
        self._changes: Dict[HolidaysAndSpecialSessions, Changes[Any]] = {k: Changes[k.value[1]](schema=k.value[2]) for k in HolidaysAndSpecialSessions}

    def clear_day(self, date: pd.Timestamp, day_type: Optional[HolidaysAndSpecialSessions] = None) -> Self:
        """
        Clear a day from the change set.

        Parameters
        ----------
        date : pd.Timestamp
            The date to clear.
        day_type : Optional[HolidaysAndSpecialSessions]
            The day type to clear. If None, all day types will be cleared.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        if day_type is None:
            # Clear for all day types.
            for c in self.changes.values():
                c.clear_day(date)
        else:
            # Clear for the given day type.
            self.changes[day_type].clear_day(date)

        return self

    def clear(self) -> Self:
        """
        Clear all changes.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        # Clear all changes for all day types.
        for c in self.changes.values():
            c.clear()

        return self

    def add_day(self, date: pd.Timestamp, value: Any, day_type: HolidaysAndSpecialSessions, strict: bool = False) -> Self:
        """
        Add a day to the change set.

        Parameters
        ----------
        date : pd.Timestamp
            The date to add.
        value : Any
            The value to add.
        day_type : HolidaysAndSpecialSessions
            The day type to add.
        strict : bool
            If True, raise ValueError if adding the given date would make the changeset inconsistent. If False, ensure
            that the changeset remains consistent with the day added, by removing the date anywhere else in the
            changeset, where required.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        # Check if the given date is already added somewhere.
        is_added = any(date in c.add.keys() and k != day_type for k, c in self.changes.items())

        # Exit early if strict is True and the date is already added somewhere.
        if strict and is_added:
            raise ValueError(f'Adding the given date {date} for day type {day_type} would make the changeset inconsistent.')

        # Add the day to the change set. This may raise ValueError if the date is already in the days to remove for the
        # given day type.
        self.changes[day_type].add_day(date, value, strict)

        if not strict and is_added:
            # Remove the date from the changeset for all other day types.
            for k, c in self.changes.items():
                if k != day_type and date in c.add.keys():
                    c.clear_day(date)

        return self

    def remove_day(self, date: pd.Timestamp, day_type: Optional[HolidaysAndSpecialSessions] = None, strict: bool = False) -> Self:
        """
        Remove a day from the change set.

        Parameters
        ----------
        date : pd.Timestamp
            The date to remove.
        day_type : HolidaysAndSpecialSessions
            The day type to remove.
        strict : bool
            If True, raise ValueError if removing the given date would make the changeset inconsistent. If False, ensure
            that the changeset remains consistent by removing the day from the dates to add for any day type where it is
            going to be added to the days to remove.

        Returns
        -------
        ExchangeCalendarChangeSet : self

        Raises
        ------
        ValueError
            If removing the given date would make the changeset inconsistent.
        """
        if day_type is not None:
            self.changes[day_type].remove_day(date, strict)
        else:
            # Remove for all day types.
            for c in self.changes.values():
                c.remove_day(date, strict)

        return self

    def is_empty(self):
        """
        Return True if there are no changes.

        Returns
        -------
        bool
            True if there are no changes.
        """
        return not any(changes.add or changes.remove for changes in self.changes.values())

    def is_consistent(self):
        """
        Return True if the change set is consistent.

        A change set is consistent iff
        - the dates of all days to add do not overlap across the different day types, and
        - the dates to add and the days to remove do not overlap for each day type, respectively.

        Returns
        -------
        bool
            True if the change set is consistent, False otherwise.
        """
        # Check if all contained changes are consistent for each day type.
        if not all(changes.is_consistent() for changes in self.changes.values()):
            return False

        # Get all dates to add.
        dates_to_add = sorted(list(itertools.chain.from_iterable(changes.add.keys() for changes in self.changes.values())))

        # Check if there are any overlapping dates to add.
        if len(dates_to_add) != len(set(dates_to_add)):
            # Duplicates in the dates to add. This is invalid since the same day cannot be added multiple times with a
            # different day type each.
            return False

        if any([changes.add.keys() & changes.remove for changes in self.changes.values()]):
            return False

        return True

    def __copy__(self) -> 'ChangeSet':
        """
        Return a shallow copy of the change set.

        Returns
        -------
        ChangeSet
            The shallow copy.
        """
        cs = ChangeSet()
        cs._changes = self.changes

        return cs

    def __deepcopy__(self, memo) -> 'ChangeSet':
        """
        Return a deep copy of the change set.

        Returns
        -------
        ChangeSet
            The deep copy.
        """
        cs = ChangeSet()
        cs._changes = deepcopy(self._changes)

        return cs

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

        for day_type in HolidaysAndSpecialSessions:
            # Get the dates to add for the day type.
            dates_to_add = cs._changes[day_type].add.keys()
            # Loop over all day types.
            for day_type0 in HolidaysAndSpecialSessions:
                if day_type0 != day_type:
                    # Add the dates to add for day_type to the dates to remove for day_type0.
                    for date in dates_to_add:
                        cs.remove_day(date, day_type0, strict=True)

        return cs

    def __eq__(self, other):
        if not isinstance(other, ChangeSet):
            return False

        return self.changes == other.changes

    def __str__(self):
        changes_str = ", ".join([f'{k.name}: {c}' for k, c in self.changes.items() if not c.is_empty()])
        return f'ChangeSet({changes_str})'

    @classmethod
    def from_dict(cls, d: dict) -> "ChangeSet":
        """
        Create a change set from a dictionary.

        The changes represented by the input dictionary need to result in a consistent change set. Otherwise, a
        ValueError is raised.

        Parameters
        ----------
        d : dict
            The dictionary to create the change set from.

        Returns
        -------
        ExchangeCalendarChangeSet
            The created change set.

        Raises
        ------
        ValueError
            If the given dictionary does not represent a consistent change set.
        """
        try:
            # Validate the input dictionary.
            d = _SCHEMA.validate(d)
        except Exception as e:
            raise ValueError(f"Dictionary does not satisfy expected schema.") from e

        # Create empty change set.
        cs: ChangeSet = cls()

        # Add the changes for each day type.
        for day_type_str, changes_incoming in d.items():
            try:
                # Convert the day type string to the corresponding enum value.
                day_type: HolidaysAndSpecialSessions = HolidaysAndSpecialSessions.from_str(day_type_str)
            except ValueError as e:
                raise ValueError(f"Invalid day type '{day_type_str}' in dictionary.") from e

            if changes_incoming.get('add') is not None:
                for item in changes_incoming.get('add'):
                    cs.add_day(date=item['date'], value=item['value'], day_type=day_type, strict=True)

            if changes_incoming.get('remove') is not None:
                for date in changes_incoming.get('remove'):
                    cs.remove_day(date=date, day_type=day_type, strict=True)

        return cs
