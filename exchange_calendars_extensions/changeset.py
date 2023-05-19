import datetime as dt
import itertools
from collections import namedtuple
from dataclasses import field, dataclass
from enum import Enum
from typing import Tuple, Set, Generic, TypeVar, Any, Dict, Self, TypedDict, Union
from types import MappingProxyType
from schema import Schema, Optional, Use

import pandas as pd

T = TypeVar('T')


@dataclass
class Changes(Generic[T]):
    
    @property
    def add(self) -> Dict[pd.Timestamp, T]:
        return MappingProxyType(self._add)
    
    @property
    def remove(self) -> Set[pd.Timestamp]:
        return frozenset(self._remove)

    def __init__(self, schema: Schema):
        self._schema = schema
        self._add = dict()
        self._remove = set()
        
    def _remove_from_add(self, date: pd.Timestamp) -> None:
        # Check if holiday to remove is already in the dictionary of holidays to add.
        if self._add.get(date) is not None:
            # Remove element from the dictionary.
            del self._add[date]
            
    def _remove_from_remove(self, date: pd.Timestamp) -> None:
        # Check if holiday to add is already in the set of holidays to remove.
        if date in self._remove:
            # Remove the holiday from the set of holidays to remove.
            self._remove.remove(date)

    def add_day(self, date: pd.Timestamp, value: T, strict: bool) -> Self:
        # Validate value against schema.
        value = self._schema.validate(value)

        # Ensure consistency by removing from days to remove, maybe.
        if not strict:
            self._remove_from_remove(date)

        # Add the holiday to the set of holidays to add. Also overwrites any previous entry for the date.
        self._add[date] = value
        
        # Check consistency.
        if not self.is_consistent():
            raise ValueError(f'Changes are not consistent: {self}.')
        
        return self

    def remove_day(self, date: pd.Timestamp, strict: bool) -> Self:
        # Ensure consistency by removing from days to add, maybe.
        if not strict:
            self._remove_from_add(date)

        # Add the holiday to the set of holidays to remove. Will be a no-op if the date is already in the set.
        self._remove.add(date)
        
        # Check consistency.
        if not self.is_consistent():
            raise ValueError(f'Changes are not consistent: {self}.')
        
        return self
    
    def reset_day(self, date: pd.Timestamp) -> Self:
        # Remove the holiday from the set of holidays to add.
        self._remove_from_add(date)

        # Remove the holiday from the set of holidays to remove.
        self._remove_from_remove(date)
        
        return self

    def is_consistent(self) -> bool:
        """
        Check if the changeset is consistent.

        Returns
        -------
        bool
            True if the changeset is consistent, False otherwise.
        """
        # Check if any dates are in both the set of holidays to add and the set of holidays to remove.
        return len(self.add.keys() & self.remove) == 0

    def __eq__(self, other) -> bool:
        if not isinstance(other, Changes):
            return False

        return self.add == other.add and self.remove == other.remove
    
    def __str__(self) -> str:
        return f'Changes(add={self.add}, remove={self.remove})'


def _to_time(input: Union[str, dt.time]) -> dt.time:
    if isinstance(input, dt.time):
        return input
    try:
        return dt.datetime.strptime(input, '%H:%M').time()
    except ValueError:
        return dt.datetime.strptime(input, '%H:%M:%S').time()


DaySpec = TypedDict('DAY_SPEC', {'name': str})
_DaySchema = Schema({'name': str})

DaySpecWithTime = TypedDict('DAY_SPEC_WITH_TIME', {'name': str, 'time': dt.time})
_DayWithTimeSchema = Schema({'name': str, 'time': Use(_to_time)})

_EnumValue = namedtuple('EnumValue', ['value', 'spec', 'schema'])


class HolidaysAndSpecialSessions(Enum):

    HOLIDAY = (1, DaySpec, _DaySchema)
    SPECIAL_OPEN = (2, DaySpecWithTime, _DayWithTimeSchema)
    SPECIAL_CLOSE = (3, DaySpecWithTime, _DayWithTimeSchema)
    MONTHLY_EXPIRY = (4, DaySpec, _DaySchema)
    QUARTERLY_EXPIRY = (5, DaySpec, _DaySchema)

    @staticmethod
    def from_str(key: str):
        return HolidaysAndSpecialSessions[key.upper()]


_SCHEMA = Schema({
    Optional('holiday'): {Optional('add'): [{'date': Use(pd.Timestamp), 'value': _DaySchema}], Optional('remove'): [Use(pd.Timestamp)]},
    Optional('special_open'): {Optional('add'): [{'date': Use(pd.Timestamp), 'value': _DayWithTimeSchema}], Optional('remove'): [Use(pd.Timestamp)]},
    Optional('special_close'): {Optional('add'): [{'date': Use(pd.Timestamp), 'value': _DayWithTimeSchema}], Optional('remove'): [Use(pd.Timestamp)]},
    Optional('monthly_expiry'): {Optional('add'): [{'date': Use(pd.Timestamp), 'value': _DaySchema}], Optional('remove'): [Use(pd.Timestamp)]},
    Optional('quarterly_expiry'): {Optional('add'): [{'date': Use(pd.Timestamp), 'value': _DaySchema}], Optional('remove'): [Use(pd.Timestamp)]},
})


@dataclass
class ChangeSet:
    """
    Represents a modification to an existing exchange calendar.

    Parameters
    ----------
    changes : Dict[HolidaysAndSpecialSessions, Changes[Any]]
        The changes per day type.
    """
    changes: Dict[HolidaysAndSpecialSessions, Changes[Any]] = field(default_factory=lambda: {k: Changes[k.value[1]](schema=k.value[2]) for k in
                                                                                             HolidaysAndSpecialSessions})

    def clear(self) -> Self:
        """
        Clear all changes.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        for changes in self.changes.values():
            changes.add.clear()
            changes.remove.clear()

        return self

    def add_day(self, day_type: HolidaysAndSpecialSessions, date: pd.Timestamp, value: Any, strict: bool = False) -> Self:
        """
        Add a day to the change set.

        Parameters
        ----------
        day_type : HolidaysAndSpecialSessions
            The day type to add.
        date : pd.Timestamp
            The date to add.
        value : Any
            The value to add.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        self.changes[day_type].add_day(date, value, strict)
        self._check_consistent()
        return self

    def remove_day(self, day_type: HolidaysAndSpecialSessions, date: pd.Timestamp, strict: bool = False) -> Self:
        """
        Remove a day from the change set.

        Parameters
        ----------
        day_type : HolidaysAndSpecialSessions
            The day type to remove.
        date : pd.Timestamp
            The date to remove.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        self.changes[day_type].remove_day(date, strict)
        self._check_consistent()
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

    def _check_consistent(self):
        if not self.is_consistent():
            raise ValueError("Change set is not consistent.")

    def __eq__(self, other):
        if not isinstance(other, ChangeSet):
            return False

        return self.changes == other.changes

    @classmethod
    def from_dict(cls, d: dict) -> "ChangeSet":
        try:
            d = _SCHEMA.validate(d)

            cs: ChangeSet = cls()

            for day_type_str, changes_incoming in d.items():
                day_type: HolidaysAndSpecialSessions = HolidaysAndSpecialSessions.from_str(day_type_str)
                changes: Changes = cs.changes[day_type]

                if changes_incoming.get('add') is not None:
                    for item in changes_incoming.get('add'):
                        changes.add_day(item['date'], item['value'], strict=True)

                if changes_incoming.get('remove') is not None:
                    for date in changes_incoming.get('remove'):
                        changes.remove_day(date, strict=True)
        except Exception as e:
            raise ValueError(f"Invalid change set.") from e

        cs._check_consistent()

        return cs
