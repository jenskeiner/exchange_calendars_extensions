from dataclasses import field, dataclass
from typing import Tuple, Set

import pandas as pd
from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday


@dataclass
class ExchangeCalendarChangeSet:
    """A modification to an existing calendar.

    Parameters
    ----------
    holidays_add : Set[Tuple[pd.Timestamp, str]]
        List of holidays to add.
    holidays_remove : Set[pd.Timestamp]
        List of holidays to remove.
    """
    holidays_add: Set[Tuple[pd.Timestamp, str]] = field(default_factory=list)
    holidays_remove: Set[pd.Timestamp] = field(default_factory=list)

    def apply(self, calendar: ExchangeCalendar):
        # Add holidays.

        rules = calendar.regular_holidays.rules

        for ts, name in self.holidays_add:
            # Check if any rule collides with date.
            for rule in rules:
                if len(rule.dates(start_date=ts, end_date=ts)) > 0:
                    print(f"Warning: {rule} collides with {ts} {name}.")
                    continue
            rules.append(Holiday(name, year=ts.year, month=ts.month, day=ts.day))

        cal = HolidayCalendar(rules)

        @property
        def regular_holidays(self):
            return cal

        # Overwrite regular_holidays property on calendar so that it returns cal instead of the original.
        setattr(calendar, "regular_holidays", regular_holidays)
