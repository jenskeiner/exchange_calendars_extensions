import datetime
from dataclasses import field, dataclass
from typing import Tuple, Set

import pandas as pd


@dataclass
class ExchangeCalendarChangeSet:
    """A modification to an existing calendar.

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
    
    def clear(self):
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
