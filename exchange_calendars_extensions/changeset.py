import datetime
from dataclasses import field, dataclass
from enum import Enum, auto
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
    HOLIDAY = str
    SPECIAL_OPEN = Tuple[datetime.time, str]
    SPECIAL_CLOSE = Tuple[datetime.time, str]
    MONTHLY_EXPIRY = str
    QUARTERLY_EXPIRY = str


@dataclass
class ExchangeCalendarChangeSet:
    """
    Represents a modification to an existing exchange calendar.

    Parameters
    ----------
    holidays_add : Set[Tuple[pd.Timestamp, str]]
        Set of holidays to add.
    holidays_remove : Set[pd.Timestamp]
        Set of holidays to remove.
    special_closes_add : Set[Tuple[pd.Timestamp, datetime.time, str]]
        Set of special closes to add.
    special_closes_remove : Set[pd.Timestamp]
        Set of special closes to remove.
    special_opens_add : Set[Tuple[pd.Timestamp, datetime.time, str]]
        Set of special opens to add.
    special_opens_remove : Set[pd.Timestamp]
        Set of special opens to remove.
    quarterly_expiries_add : Set[Tuple[pd.Timestamp, str]]
        Set of quarterly expiries to add.
    quarterly_expiries_remove : Set[pd.Timestamp]
        Set of quarterly expiries to remove.
    monthly_expiries_add : Set[Tuple[pd.Timestamp, str]]
        Set of monthly expiries to add.
    monthly_expiries_remove : Set[pd.Timestamp]
        Set of monthly expiries to remove.
    """
    changes: dict[HolidaysAndSpecialSessions, Changes[Any]] = field(default_factory=lambda: {k: Changes[k.value]() for k in HolidaysAndSpecialSessions})

    #holidays_add: Set[Tuple[pd.Timestamp, str]] = field(default_factory=set)
    #holidays_remove: Set[pd.Timestamp] = field(default_factory=set)
    
    special_closes_add: Set[Tuple[pd.Timestamp, datetime.time, str]] = field(default_factory=set)
    special_closes_remove: Set[pd.Timestamp] = field(default_factory=set)

    special_opens_add: Set[Tuple[pd.Timestamp, datetime.time, str]] = field(default_factory=set)
    special_opens_remove: Set[pd.Timestamp] = field(default_factory=set)
    
    quarterly_expiries_add: Set[Tuple[pd.Timestamp, str]] = field(default_factory=set)
    quarterly_expiries_remove: Set[pd.Timestamp] = field(default_factory=set)
    
    monthly_expiries_add: Set[Tuple[pd.Timestamp, str]] = field(default_factory=set)
    monthly_expiries_remove: Set[pd.Timestamp] = field(default_factory=set)
    
    def clear(self) -> "ExchangeCalendarChangeSet":
        """
        Clear all changes.

        Returns
        -------
        ExchangeCalendarChangeSet : self
        """
        self.holidays_add.clear()
        self.holidays_remove.clear()
        self.special_closes_add.clear()
        self.special_closes_remove.clear()
        self.special_opens_add.clear()
        self.special_opens_remove.clear()
        self.quarterly_expiries_add.clear()
        self.quarterly_expiries_remove.clear()
        self.monthly_expiries_add.clear()
        self.monthly_expiries_remove.clear()

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
        return not (any([
            #self.holidays_add,
            #self.holidays_remove,
            self.special_closes_add,
            self.special_closes_remove,
            self.special_opens_add,
            self.special_opens_remove,
            self.quarterly_expiries_add,
            self.quarterly_expiries_remove,
            self.monthly_expiries_add,
            self.monthly_expiries_remove,
        ]) or any(changes.add or changes.remove for changes in self.changes.values()))
