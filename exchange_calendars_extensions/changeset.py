import datetime
from dataclasses import field, dataclass
from typing import Tuple, Set

import pandas as pd


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

    holidays_add: Set[Tuple[pd.Timestamp, str]] = field(default_factory=set)
    holidays_remove: Set[pd.Timestamp] = field(default_factory=set)
    
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

        return self

    def is_empty(self):
        """
        Return True if there are no changes.

        Returns
        -------
        bool
            True if there are no changes.
        """
        return not any([
            self.holidays_add,
            self.holidays_remove,
            self.special_closes_add,
            self.special_closes_remove,
            self.special_opens_add,
            self.special_opens_remove,
            self.quarterly_expiries_add,
            self.quarterly_expiries_remove,
            self.monthly_expiries_add,
            self.monthly_expiries_remove,
        ])
