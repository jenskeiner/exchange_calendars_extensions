import datetime as dt
from collections.abc import Collection, Iterable
from zoneinfo import ZoneInfo

import exchange_calendars as ec
import pandas as pd
from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
from pandas.tseries.holiday import next_monday

import exchange_calendars_extensions as ecx
from exchange_calendars_extensions import DateLike

REGULAR_DAY_DT = DateLike("2023-07-03")
WEEKEND_DAY_DT = DateLike("2023-07-02")
HOLIDAY_REGULAR_DT = DateLike("2023-01-02")
HOLIDAY_REGULAR_NAME = "Holiday 0"
HOLIDAY_ADHOC_DT = DateLike("2023-02-01")
SPECIAL_CLOSE_REGULAR_DT = DateLike("2023-03-01")
SPECIAL_CLOSE_REGULAR_NAME = "Special Close 0"
SPECIAL_CLOSE_ADHOC_DT = DateLike("2023-04-03")
SPECIAL_OPEN_REGULAR_DT = DateLike("2023-05-03")
SPECIAL_OPEN_REGULAR_NAME = "Special Open 0"
SPECIAL_OPEN_ADHOC_DT = DateLike("2023-06-01")
OPEN_REGULAR = dt.time(9, 00)
OPEN_SPECIAL_REGULAR = dt.time(10, 00)
OPEN_SPECIAL_AD_HOC = dt.time(11, 00)
OPEN_SPECIAL_CUSTOM = dt.time(12, 00)
CLOSE_REGULAR = dt.time(17, 30)
CLOSE_SPECIAL_REGULAR = dt.time(16, 30)
CLOSE_SPECIAL_AD_HOC = dt.time(15, 30)
CLOSE_SPECIAL_CUSTOM = dt.time(14, 30)


def create_test_calendar_class(
    *,
    holidays: Iterable[pd.Timestamp] | None = (HOLIDAY_REGULAR_DT,),
    adhoc_holidays: Iterable[pd.Timestamp] | None = (HOLIDAY_ADHOC_DT,),
    regular_special_close: dt.time | None = CLOSE_SPECIAL_REGULAR,
    special_closes: Collection[tuple[dt.time, Collection[pd.Timestamp]]] | None = (
        (CLOSE_SPECIAL_REGULAR, (SPECIAL_CLOSE_REGULAR_DT,)),
    ),
    adhoc_special_closes: Collection[
        tuple[dt.time, pd.Timestamp | Collection[pd.Timestamp]]
    ]
    | None = ((CLOSE_SPECIAL_AD_HOC, SPECIAL_CLOSE_ADHOC_DT),),
    regular_special_open: dt.time | None = OPEN_SPECIAL_REGULAR,
    special_opens: Collection[tuple[dt.time, Collection[pd.Timestamp]]] | None = (
        (OPEN_SPECIAL_REGULAR, (SPECIAL_OPEN_REGULAR_DT,)),
    ),
    adhoc_special_opens: Collection[
        tuple[dt.time, pd.Timestamp | Collection[pd.Timestamp]]
    ]
    | None = ((dt.time(11, 00), SPECIAL_OPEN_ADHOC_DT),),
    weekmask: str | None = "1111100",
) -> type[ExchangeCalendar]:
    def ensure_list(obj):
        """Check if an object is iterable."""
        try:
            iter(obj)
        except Exception:
            return [obj]
        else:
            return list(obj)

    # Define a test calendar class, subclassing the ExchangeCalendar class. Within the class body, define the
    # holidays, special closes and special opens, as well as the weekmask, based on the parameters passed to the
    # factory.
    class TestCalendar(ExchangeCalendar):
        # Regular open/close times.
        open_times = ((None, OPEN_REGULAR),)
        close_times = ((None, CLOSE_REGULAR),)

        # Special open/close times.
        regular_early_close = regular_special_close
        regular_late_open = regular_special_open

        # Name.
        name = "TEST"

        # Timezone.
        tz = ZoneInfo("CET")

        # Holidays.
        @property
        def regular_holidays(self):
            return HolidayCalendar(
                [
                    Holiday(name=f"Holiday {i}", month=ts.month, day=ts.day)
                    for i, ts in enumerate(holidays)
                ]
                if holidays
                else []
            )

        @property
        def adhoc_holidays(self):
            return adhoc_holidays if adhoc_holidays else []

        @property
        def special_closes(self):
            return [
                (
                    x[0],
                    HolidayCalendar(
                        [
                            Holiday(
                                name=f"Special Close {i}",
                                month=ts.month,
                                day=ts.day,
                                observance=next_monday,
                            )
                            for i, ts in enumerate(x[1])
                        ]
                    ),
                )
                for x in special_closes or []
            ]

        @property
        def special_closes_adhoc(self):
            return [
                (x[0], pd.DatetimeIndex(ensure_list(x[1])))
                for x in adhoc_special_closes or []
            ]

        @property
        def special_opens(self):
            return [
                (
                    x[0],
                    HolidayCalendar(
                        [
                            Holiday(
                                name=f"Special Open {i}",
                                month=ts.month,
                                day=ts.day,
                                observance=next_monday,
                            )
                            for i, ts in enumerate(x[1])
                        ]
                    ),
                )
                for x in special_opens or []
            ]

        @property
        def special_opens_adhoc(self):
            return [
                (x[0], pd.DatetimeIndex(ensure_list(x[1])))
                for x in adhoc_special_opens or []
            ]

        # Weekmask.
        @property
        def weekmask(self):
            return weekmask

    return TestCalendar


TEST_CALENDAR_CLASS_DEFAULT = create_test_calendar_class()


def add_extended_calendar_class(
    *,
    cls: type[ExchangeCalendar],
    day_of_week_expiry: int | None = None,
    name: str = "TEST",
):
    ecx.remove_extensions()
    ec.register_calendar_type(name, cls, force=True)
    ecx.register_extension(name, day_of_week_expiry=day_of_week_expiry)
    ecx.change_calendar(name, {}, mode="replace")
    ecx.apply_extensions()


def add_test_calendar():
    add_extended_calendar_class(cls=TEST_CALENDAR_CLASS_DEFAULT, day_of_week_expiry=4)
