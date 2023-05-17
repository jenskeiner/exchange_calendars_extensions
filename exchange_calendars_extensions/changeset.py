import datetime
import itertools
from dataclasses import field, dataclass
from enum import Enum
from typing import Tuple, Set, Generic, TypeVar, Any, Dict

import pandas as pd

T = TypeVar('T')


@dataclass
class Changes(Generic[T]):
    add: Dict[pd.Timestamp, T] = field(default_factory=dict)
    remove: Set[pd.Timestamp] = field(default_factory=set)

    def add_day(self, date: pd.Timestamp, value: T):
        # Check if holiday to add is already in the set of holidays to remove.
        if date in self.remove:
            # Remove the holiday from the set of holidays to remove.
            self.remove.remove(date)

        # Add the holiday to the set of holidays to add. Also overwrites any previous entry for the date.
        self.add[date] = value

    def remove_day(self, date: pd.Timestamp):
        # Check if holiday to remove is already in the dictionary of holidays to add.
        if self.add.get(date) is not None:
            # Remove element from the dictionary.
            del self.add[date]

        # Add the holiday to the set of holidays to remove. Will be a no-op if the date is already in the set.
        self.remove.add(date)


class HolidaysAndSpecialSessions(Enum):
    HOLIDAY = Tuple[str]
    SPECIAL_OPEN = Tuple[datetime.time, str]
    SPECIAL_CLOSE = Tuple[datetime.time, str]
    MONTHLY_EXPIRY = Tuple[str]
    QUARTERLY_EXPIRY = Tuple[str]


@dataclass
class ChangeSet:
    """
    Represents a modification to an existing exchange calendar.

    Parameters
    ----------
    changes : Dict[HolidaysAndSpecialSessions, Changes[Any]]
        The changes per day type.
    """
    changes: Dict[HolidaysAndSpecialSessions, Changes[Any]] = field(default_factory=lambda: {k: Changes[k.value]() for k in
                                                                                             HolidaysAndSpecialSessions})

    def clear(self) -> "ChangeSet":
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
