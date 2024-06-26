import datetime
from collections import OrderedDict
from collections.abc import Iterable
from datetime import time
from typing import Optional, Union

import pandas as pd
import pytest
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
from pandas.tseries.holiday import next_monday
from pytz import timezone

from exchange_calendars_extensions.api.changes import DayMeta

HOLIDAY_0 = "Holiday 0"
SPECIAL_OPEN_0 = "Special Open 0"
SPECIAL_CLOSE_0 = "Special Close 0"
AD_HOC_HOLIDAY = "ad-hoc holiday"
AD_HOC_SPECIAL_OPEN = "ad-hoc special open"
AD_HOC_SPECIAL_CLOSE = "ad-hoc special close"
WEEKEND_DAY = "weekend day"
QUARTERLY_EXPIRY = "quarterly expiry"
MONTHLY_EXPIRY = "monthly expiry"
LAST_TRADING_DAY_OF_MONTH = "last trading day of month"
LAST_REGULAR_TRADING_DAY_OF_MONTH = "last regular trading day of month"
ADDED_HOLIDAY = "Added holiday"
ADDED_SPECIAL_OPEN = "Added Special Open"
ADDED_SPECIAL_CLOSE = "Added Special Close"
INSERTED_HOLIDAY = "Inserted Holiday"


def apply_extensions():
    """Apply the extensions to the exchange_calendars module."""
    import exchange_calendars_extensions.core as ecx

    ecx.apply_extensions()


def add_test_calendar_and_apply_extensions(
    holidays: Optional[Iterable[pd.Timestamp]] = (pd.Timestamp("2023-01-01"),),
    adhoc_holidays: Optional[Iterable[pd.Timestamp]] = (pd.Timestamp("2023-02-01"),),
    regular_special_close: Optional[time] = time(14, 00),
    special_closes: Optional[
        Iterable[tuple[datetime.time, Union[Iterable[pd.Timestamp], int]]]
    ] = ((time(14, 00), (pd.Timestamp("2023-03-01"),)),),
    adhoc_special_closes: Optional[
        Iterable[tuple[datetime.time, Union[pd.Timestamp, Iterable[pd.Timestamp]]]]
    ] = ((time(14, 00), pd.Timestamp("2023-04-03")),),
    regular_special_open: Optional[time] = time(11, 00),
    special_opens: Optional[
        Iterable[tuple[datetime.time, Union[Iterable[pd.Timestamp], int]]]
    ] = ((time(11, 00), (pd.Timestamp("2023-05-01"),)),),
    adhoc_special_opens: Optional[
        Iterable[tuple[datetime.time, Union[pd.Timestamp, Iterable[pd.Timestamp]]]]
    ] = ((time(11, 00), pd.Timestamp("2023-06-01")),),
    weekmask: Optional[str] = "1111100",
    day_of_week_expiry: Optional[int] = 4,
):
    def ensure_list(obj):
        """Check if an object is iterable."""
        try:
            iter(obj)
        except Exception:
            return [obj]
        else:
            return list(obj)

    import exchange_calendars as ec

    # Define a test calendar class, subclassing the ExchangeCalendar class. Within the class body, define the
    # holidays, special closes and special opens, as well as the weekmask, based on the parameters passed to the
    # factory.
    class TestCalendar(ec.ExchangeCalendar):
        # Regular open/close times.
        open_times = ((None, time(9)),)
        close_times = ((None, time(17, 30)),)

        # Special open/close times.
        regular_early_close = regular_special_close
        regular_late_open = regular_special_open

        # Name.
        name = "TEST"

        # Timezone.
        tz = timezone("CET")

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
            return (
                list(
                    map(
                        lambda x: (
                            x[0],
                            x[1]
                            if isinstance(x[1], int)
                            else HolidayCalendar(
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
                        ),
                        special_closes,
                    )
                )
                if special_closes
                else []
            )

        @property
        def special_closes_adhoc(self):
            return (
                list(
                    map(
                        lambda x: (x[0], pd.DatetimeIndex(ensure_list(x[1]))),
                        adhoc_special_closes,
                    )
                )
                if adhoc_special_closes
                else []
            )

        @property
        def special_opens(self):
            return (
                list(
                    map(
                        lambda x: (
                            x[0],
                            x[1]
                            if isinstance(x[1], int)
                            else HolidayCalendar(
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
                        ),
                        special_opens,
                    )
                )
                if special_opens
                else []
            )

        @property
        def special_opens_adhoc(self):
            return (
                list(
                    map(
                        lambda x: (x[0], pd.DatetimeIndex(ensure_list(x[1]))),
                        adhoc_special_opens,
                    )
                )
                if adhoc_special_opens
                else []
            )

        # Weekmask.
        @property
        def weekmask(self):
            return weekmask

    ec.register_calendar_type("TEST", TestCalendar)

    import exchange_calendars_extensions.core as ecx

    ecx.register_extension("TEST", day_of_week_expiry=day_of_week_expiry)

    ecx.apply_extensions()


@pytest.mark.isolated
def test_unmodified_calendars():
    """Test that calendars are unmodified when the module is just imported, without calling apply_extensions()"""
    import exchange_calendars_extensions.core as ecx

    import exchange_calendars as ec

    c = ec.get_calendar("XETR")

    # Check if returned Calendar is of expected type.
    assert isinstance(c, ec.ExchangeCalendar)

    # Check if returned Calendar is not of extended type.
    assert not isinstance(c, ecx.ExtendedExchangeCalendar)
    assert not isinstance(c, ecx.ExchangeCalendarExtensions)


@pytest.mark.isolated
def test_apply_extensions():
    """Test that calendars are modified when apply_extensions() is called"""
    apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    c = ec.get_calendar("XETR")

    # Check if returned Calendar is of expected types.
    assert isinstance(c, ec.ExchangeCalendar)
    assert isinstance(c, ecx.ExtendedExchangeCalendar)
    assert isinstance(c, ecx.ExchangeCalendarExtensions)


@pytest.mark.isolated
def test_extended_calendar_xetr():
    """Test the additional properties of the extended XETR calendar."""
    apply_extensions()

    import exchange_calendars as ec

    c = ec.get_calendar("XETR")

    # Check if additional properties are present.
    assert hasattr(c, "holidays_all")
    assert isinstance(c.holidays_all, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "special_opens_all")
    assert isinstance(c.special_opens_all, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "special_closes_all")
    assert isinstance(c.special_closes_all, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "weekend_days")
    assert isinstance(c.weekend_days, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "monthly_expiries")
    assert isinstance(c.monthly_expiries, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "quarterly_expiries")
    assert isinstance(c.quarterly_expiries, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "last_trading_days_of_months")
    assert isinstance(
        c.last_trading_days_of_months, ec.exchange_calendar.HolidayCalendar
    )

    assert hasattr(c, "last_regular_trading_days_of_months")
    assert isinstance(
        c.last_regular_trading_days_of_months, ec.exchange_calendar.HolidayCalendar
    )


@pytest.mark.isolated
def test_extended_calendar_test():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    c = ec.get_calendar("TEST")

    assert isinstance(c, ecx.ExtendedExchangeCalendar)

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Verify regular holidays for 2022, 2023, and 2024.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Verify adhoc holidays.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Verify special closes for 2022, 2023, and 2024.
    assert len(c.special_closes) == 1
    assert len(c.special_closes[0]) == 2
    assert c.special_closes[0][0] == datetime.time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Verify adhoc special closes.
    assert c.special_closes_adhoc == [
        (datetime.time(14, 0), pd.DatetimeIndex([pd.Timestamp("2023-04-03")]))
    ]

    # Verify special opens for 2022, 2023, and 2024.
    assert len(c.special_opens) == 1
    assert len(c.special_opens[0]) == 2
    assert c.special_opens[0][0] == datetime.time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Verify adhoc special opens.
    assert c.special_opens_adhoc == [
        (datetime.time(11, 0), pd.DatetimeIndex([pd.Timestamp("2023-06-01")]))
    ]

    # Verify additional holiday calendars.

    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    assert (
        c.weekend_days.holidays(
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-31"),
            return_name=True,
        )
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2023-01-01"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-07"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-08"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-14"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-15"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-21"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-22"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-28"): WEEKEND_DAY,
                    pd.Timestamp("2023-01-29"): WEEKEND_DAY,
                }
            )
        )
        .empty
    )

    assert (
        c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-18"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-06-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-09-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-12-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-03-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-06-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-09-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-12-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-03-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-06-21"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-09-20"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-12-20"): QUARTERLY_EXPIRY,
                }
            )
        )
        .empty
    )

    assert (
        c.monthly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-02-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-04-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-05-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-07-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-08-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-10-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-11-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-01-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-02-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-04-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-05-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-07-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-08-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-10-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-11-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-01-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-02-16"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-04-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-05-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-07-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-08-16"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-10-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-11-15"): MONTHLY_EXPIRY,
                }
            )
        )
        .empty
    )

    assert (
        c.last_trading_days_of_months.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-02-28"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-03-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-04-29"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-05-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-06-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-07-29"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-08-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-09-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-10-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-11-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-12-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-01-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-02-28"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-03-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-04-28"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-05-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-06-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-07-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-08-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-09-29"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-10-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-11-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-12-29"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-01-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-02-29"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-03-29"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-04-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-05-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-06-28"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-07-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-08-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-09-30"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-10-31"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-11-29"): LAST_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-12-31"): LAST_TRADING_DAY_OF_MONTH,
                }
            )
        )
        .empty
    )

    assert (
        c.last_regular_trading_days_of_months.holidays(
            start=start, end=end, return_name=True
        )
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-02-28"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-03-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-04-29"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-05-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-06-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-07-29"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-08-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-09-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-10-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-11-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2022-12-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-01-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-02-28"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-03-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-04-28"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-05-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-06-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-07-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-08-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-09-29"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-10-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-11-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2023-12-29"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-01-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-02-29"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-03-29"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-04-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-05-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-06-28"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-07-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-08-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-09-30"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-10-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-11-29"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                    pd.Timestamp("2024-12-31"): LAST_REGULAR_TRADING_DAY_OF_MONTH,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_new_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_holiday("TEST", pd.Timestamp("2023-07-03"), ADDED_HOLIDAY)

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should show as regular holiday.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-07-03"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2023-07-03"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_regular_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_holiday("TEST", pd.Timestamp("2023-01-01"), ADDED_HOLIDAY)

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should overwrite existing regular holiday.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_adhoc_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_holiday("TEST", pd.Timestamp("2023-02-01"), ADDED_HOLIDAY)

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should be a regular holiday.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Overwritten ad-hoc holiday should be removed from list.
    assert c.adhoc_holidays == []

    # Added holiday should be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_existing_regular_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-01-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Removed day should no longer be in regular holidays.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Removed holiday should not affect ad-hoc holidays.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Removed day should not be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_existing_adhoc_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-02-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holidays should be untouched.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Removed holiday should no longer be in ad-hoc holidays.
    assert c.adhoc_holidays == []

    # Removed day should not be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_non_existent_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holidays should be untouched.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc holidays should be untouched.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Calendar holidays_all should be untouched.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_and_remove_new_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Add and then remove the same day. The day should stay added.
    ecx.add_holiday("TEST", pd.Timestamp("2023-07-03"), ADDED_HOLIDAY)
    ecx.remove_day("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holidays should have new day.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-07-03"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc holidays should be unchanged.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Calendar holidays_all should have new day.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2023-07-03"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_and_remove_existing_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Add and then remove the same existing holiday. The day should still be added.
    ecx.add_holiday("TEST", pd.Timestamp("2023-01-01"), ADDED_HOLIDAY)
    ecx.remove_day("TEST", pd.Timestamp("2023-01-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Updated day should be in regular holidays.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc holidays should be unchanged.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Updated day should be in holidays_all.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_and_add_new_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Remove and then add the same new holiday. The removal of a non-existent holiday should be ignored, so the day
    # should be added eventually.
    ecx.remove_day("TEST", pd.Timestamp("2023-07-03"))
    ecx.add_holiday("TEST", pd.Timestamp("2023-07-03"), ADDED_HOLIDAY)

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should show as regular holiday.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-07-03"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2023-07-03"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_and_add_existing_regular_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Remove and then add the same existent holiday. This should be equivalent to just adding (and thereby overwriting)
    # the existing regular holiday.
    ecx.remove_day("TEST", pd.Timestamp("2023-01-01"))
    ecx.add_holiday("TEST", pd.Timestamp("2023-01-01"), ADDED_HOLIDAY)

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holiday should be overwritten.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_and_add_existing_adhoc_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Remove and then add the same existent holiday. This should be equivalent to just adding (and thereby overwriting)
    # the existing regular holiday.
    ecx.remove_day("TEST", pd.Timestamp("2023-02-01"))
    ecx.add_holiday("TEST", pd.Timestamp("2023-02-01"), ADDED_HOLIDAY)

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holiday should contain the added holiday.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc holidays should be empty.
    assert c.adhoc_holidays == []

    # Added holiday should be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): ADDED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_new_special_open_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_open(
        "TEST", pd.Timestamp("2023-07-03"), time(12, 0), ADDED_SPECIAL_OPEN
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should be unchanged.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # There should be a new calendar for the added special open time.
    assert c.special_opens[1][0] == time(12, 0)
    assert (
        c.special_opens[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(pd.Series({pd.Timestamp("2023-07-03"): ADDED_SPECIAL_OPEN}))
        .empty
    )

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2023-07-03"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_new_special_open_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_open(
        "TEST", pd.Timestamp("2023-07-03"), time(11, 0), ADDED_SPECIAL_OPEN
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should be unchanged.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-07-03"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2023-07-03"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_regular_special_open_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_open(
        "TEST", pd.Timestamp("2023-05-01"), time(12, 0), ADDED_SPECIAL_OPEN
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # There should be a new calendar for the added special open time.
    assert c.special_opens[1][0] == time(12, 0)
    assert (
        c.special_opens[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(pd.Series({pd.Timestamp("2023-05-01"): ADDED_SPECIAL_OPEN}))
        .empty
    )

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_regular_special_open_with_existing_time():
    add_test_calendar_and_apply_extensions(
        special_opens=[
            (time(11, 00), [pd.Timestamp("2023-05-01")]),
            (time(12, 00), [pd.Timestamp("2023-05-04")]),
        ]
    )
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    assert c.special_opens[1][0] == time(12, 0)
    assert (
        c.special_opens[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-06"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2022-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-06"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    ecx.add_special_open(
        "TEST", pd.Timestamp("2023-05-01"), time(12, 0), ADDED_SPECIAL_OPEN
    )

    c = ec.get_calendar("TEST")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    assert c.special_opens[1][0] == time(12, 0)
    assert (
        c.special_opens[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2023-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-06"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2022-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2023-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-06"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_holiday_takes_precedence_over_weekly_special_open():
    add_test_calendar_and_apply_extensions(
        holidays=(pd.Timestamp("2023-01-02"),),  # a Monday
        special_opens=[(time(11, 0), 0)],  # Weekly early close on Mondays.
    )
    import exchange_calendars as ec

    c = ec.get_calendar("TEST")

    # Holiday on 2023-02-01 should take precedence over weekly special open on the same day.

    # Day should be in regular holidays calendar.
    assert (
        c.regular_holidays.holidays(
            start="2023-01-02", end="2023-01-02", return_name=True
        )
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2023-01-02"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Day should be in consolidated holidays calendar.
    assert (
        c.holidays_all.holidays(start="2023-01-02", end="2023-01-02", return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2023-01-02"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Day should not be in any special opens calendar.
    assert len(c.special_opens) == 1
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start="2023-01-02", end="2023-01-02", return_name=True)
        .empty
    )

    # Day should not be in consolidated special opens calendar.
    assert c.special_opens_all.holidays(
        start="2023-01-02", end="2023-01-02", return_name=True
    ).empty


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_open_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_open(
        "TEST", pd.Timestamp("2023-06-01"), time(12, 0), ADDED_SPECIAL_OPEN
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    assert c.special_opens[1][0] == time(12, 0)
    assert (
        c.special_opens[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(pd.Series({pd.Timestamp("2023-06-01"): ADDED_SPECIAL_OPEN}))
        .empty
    )

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == []

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_open_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_open(
        "TEST", pd.Timestamp("2023-06-01"), time(11, 0), ADDED_SPECIAL_OPEN
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == []

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_existing_regular_special_open():
    add_test_calendar_and_apply_extensions(
        special_opens=[
            (time(11, 00), [pd.Timestamp("2023-05-01")]),
            (time(12, 00), [pd.Timestamp("2023-05-04")]),
        ]
    )
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-05-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    assert c.special_opens[1][0] == time(12, 0)
    assert (
        c.special_opens[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-06"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2022-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-04"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-06"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_existing_ad_hoc_special_open():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-06-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == []

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_non_existent_special_open():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_new_special_close_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_close(
        "TEST", pd.Timestamp("2023-07-03"), time(15, 0), ADDED_SPECIAL_CLOSE
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special closes for regular special close time should be unchanged.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # There should be a new calendar for the added special close time.
    assert c.special_closes[1][0] == time(15, 0)
    assert (
        c.special_closes[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(pd.Series({pd.Timestamp("2023-07-03"): ADDED_SPECIAL_CLOSE}))
        .empty
    )

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2023-07-03"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_new_special_close_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_close(
        "TEST", pd.Timestamp("2023-07-03"), time(14, 0), ADDED_SPECIAL_CLOSE
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should be unchanged.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-07-03"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 0), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2023-07-03"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_regular_special_close_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_close(
        "TEST", pd.Timestamp("2023-03-01"), time(15, 0), ADDED_SPECIAL_CLOSE
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # There should be a new calendar for the added special close time.
    assert c.special_closes[1][0] == time(15, 0)
    assert (
        c.special_closes[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(pd.Series({pd.Timestamp("2023-03-01"): ADDED_SPECIAL_CLOSE}))
        .empty
    )

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_regular_special_close_with_existing_time():
    add_test_calendar_and_apply_extensions(
        special_closes=[
            (time(14, 00), [pd.Timestamp("2023-03-01")]),
            (time(15, 00), [pd.Timestamp("2023-03-04")]),
        ]
    )
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    assert c.special_closes[1][0] == time(15, 0)
    assert (
        c.special_closes[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-04"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-06"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-04"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2022-03-04"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-06"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-04"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    ecx.add_special_close(
        "TEST", pd.Timestamp("2023-03-01"), time(15, 0), ADDED_SPECIAL_CLOSE
    )

    c = ec.get_calendar("TEST")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    assert c.special_closes[1][0] == time(15, 0)
    assert (
        c.special_closes[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-04"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2023-03-06"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-04"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2022-03-04"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2023-03-06"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-04"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_holiday_takes_precedence_over_weekly_special_close():
    add_test_calendar_and_apply_extensions(
        holidays=(pd.Timestamp("2023-01-02"),),  # a Monday
        special_closes=[(time(15, 0), 0)],  # Weekly early close on Mondays.
    )
    import exchange_calendars as ec

    c = ec.get_calendar("TEST")

    # Holiday on 2023-02-01 should take precedence over weekly special open on the same day.

    # Day should be in regular holidays calendar.
    assert (
        c.regular_holidays.holidays(
            start="2023-01-02", end="2023-01-02", return_name=True
        )
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2023-01-02"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Day should be in consolidated holidays calendar.
    assert (
        c.holidays_all.holidays(start="2023-01-02", end="2023-01-02", return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2023-01-02"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Day should not be in any special closes calendar.
    assert len(c.special_closes) == 1
    assert c.special_closes[0][0] == time(15, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start="2023-01-02", end="2023-01-02", return_name=True)
        .empty
    )

    # Day should not be in consolidated special closes calendar.
    assert c.special_closes_all.holidays(
        start="2023-01-02", end="2023-01-02", return_name=True
    ).empty


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_close_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_close(
        "TEST", pd.Timestamp("2023-04-03"), time(15, 0), ADDED_SPECIAL_CLOSE
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    assert c.special_closes[1][0] == time(15, 0)
    assert (
        c.special_closes[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(pd.Series({pd.Timestamp("2023-04-03"): ADDED_SPECIAL_CLOSE}))
        .empty
    )

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == []

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_close_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_close(
        "TEST", pd.Timestamp("2023-04-03"), time(14, 0), ADDED_SPECIAL_CLOSE
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == []

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): ADDED_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_existing_regular_special_close():
    add_test_calendar_and_apply_extensions(
        special_closes=[
            (time(14, 00), [pd.Timestamp("2023-03-01")]),
            (time(15, 00), [pd.Timestamp("2023-03-04")]),
        ]
    )
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-03-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    assert c.special_closes[1][0] == time(15, 0)
    assert (
        c.special_closes[1][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-04"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-06"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-04"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2022-03-04"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-06"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-04"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_existing_ad_hoc_special_close():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-04-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == []

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_non_existent_special_close():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.remove_day("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-01"): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_quarterly_expiry():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Add quarterly expiry.
    ecx.add_quarterly_expiry(
        "TEST", pd.Timestamp("2023-06-15"), "Added Quarterly Expiry"
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Quarterly expiry dates should be empty.
    assert (
        c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-18"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-06-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-09-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-12-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-03-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-06-15"): "Added Quarterly Expiry",
                    pd.Timestamp("2023-06-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-09-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-12-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-03-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-06-21"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-09-20"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-12-20"): QUARTERLY_EXPIRY,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_remove_quarterly_expiry():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Add quarterly expiry.
    ecx.remove_day("TEST", pd.Timestamp("2023-06-16"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Quarterly expiry dates should be empty.
    assert (
        c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-18"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-06-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-09-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-12-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-03-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-09-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-12-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-03-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-06-21"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-09-20"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-12-20"): QUARTERLY_EXPIRY,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_add_monthly_expiry():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    # Add quarterly expiry.
    ecx.add_monthly_expiry("TEST", pd.Timestamp("2023-01-19"), "Added Monthly Expiry")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Quarterly expiry dates should be empty.
    assert (
        c.monthly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-02-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-04-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-05-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-07-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-08-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-10-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-11-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-01-19"): "Added Monthly Expiry",
                    pd.Timestamp("2023-01-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-02-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-04-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-05-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-07-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-08-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-10-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-11-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-01-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-02-16"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-04-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-05-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-07-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-08-16"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-10-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-11-15"): MONTHLY_EXPIRY,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_overwrite_regular_holiday_with_special_open():
    add_test_calendar_and_apply_extensions(holidays=[pd.Timestamp("2023-01-02")])
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.add_special_open(
        "TEST", pd.Timestamp("2023-01-02"), time(11, 0), ADDED_SPECIAL_OPEN
    )

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Overwritten holiday should no longer be in regular holidays.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-02"): HOLIDAY_0,
                    pd.Timestamp("2024-01-02"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc holidays should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Overwritten holiday should no longer be in holidays_all calendar.
    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-02"): HOLIDAY_0,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-02"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Added special open should be in special opens for regular time.
    assert c.special_opens[0][0] == time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-01-02"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Ad-hoc special opens should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-01-02"): ADDED_SPECIAL_OPEN,
                    pd.Timestamp("2023-05-01"): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_apply_changeset():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    changes = {
        "add": {
            "2023-01-02": {"type": "holiday", "name": INSERTED_HOLIDAY},
            "2023-05-02": {
                "type": "special_open",
                "name": "Inserted Special Open",
                "time": "11:00",
            },
            "2023-03-02": {
                "type": "special_close",
                "name": "Inserted Special Close",
                "time": "14:00",
            },
            "2023-08-17": {"type": "monthly_expiry", "name": "Inserted Monthly Expiry"},
            "2023-09-14": {
                "type": "quarterly_expiry",
                "name": "Inserted Quarterly Expiry",
            },
        },
        "remove": [
            "2023-01-01",
            "2023-05-01",
            "2023-03-01",
            "2023-08-18",
            "2023-09-15",
        ],
        "meta": {
            "2023-01-03": {"tags": ["tag1", "tag2"]},
            "2023-05-03": {"comment": "This is a comment"},
            "2023-03-03": {"tags": ["tag3", "tag´4"], "comment": "This is a comment"},
        },
    }
    ecx.update_calendar("TEST", changes)
    c = ec.get_calendar("TEST")

    assert isinstance(c, ecx.ExtendedExchangeCalendar)

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Verify regular holidays for 2022, 2023, and 2024.
    assert (
        c.regular_holidays.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    # removed: pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-02"): INSERTED_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    # Verify adhoc holidays.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Verify special closes for 2022, 2023, and 2024.
    assert len(c.special_closes) == 1
    assert len(c.special_closes[0]) == 2
    assert c.special_closes[0][0] == datetime.time(14, 0)
    assert (
        c.special_closes[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    # removed: pd.Timestamp('2023-03-01'): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-02"): "Inserted Special Close",
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    # Verify adhoc special closes.
    assert c.special_closes_adhoc == [
        (datetime.time(14, 0), pd.DatetimeIndex([pd.Timestamp("2023-04-03")]))
    ]

    # Verify special opens for 2022, 2023, and 2024.
    assert len(c.special_opens) == 1
    assert len(c.special_opens[0]) == 2
    assert c.special_opens[0][0] == datetime.time(11, 0)
    assert (
        c.special_opens[0][1]
        .holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    # removed pd.Timestamp('2023-05-01'): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-02"): "Inserted Special Open",
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    # Verify adhoc special opens.
    assert c.special_opens_adhoc == [
        (datetime.time(11, 0), pd.DatetimeIndex([pd.Timestamp("2023-06-01")]))
    ]

    # Verify additional holiday calendars.

    assert (
        c.holidays_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-01"): HOLIDAY_0,
                    # removed: pd.Timestamp("2023-01-01"): HOLIDAY_0,
                    pd.Timestamp("2023-01-02"): INSERTED_HOLIDAY,
                    pd.Timestamp("2023-02-01"): AD_HOC_HOLIDAY,
                    pd.Timestamp("2024-01-01"): HOLIDAY_0,
                }
            )
        )
        .empty
    )

    assert (
        c.special_closes_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-01"): SPECIAL_CLOSE_0,
                    # removed: pd.Timestamp('2023-03-01'): SPECIAL_CLOSE_0,
                    pd.Timestamp("2023-03-02"): "Inserted Special Close",
                    pd.Timestamp("2023-04-03"): AD_HOC_SPECIAL_CLOSE,
                    pd.Timestamp("2024-03-01"): SPECIAL_CLOSE_0,
                }
            )
        )
        .empty
    )

    assert (
        c.special_opens_all.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-05-02"): SPECIAL_OPEN_0,
                    # removed: pd.Timestamp('2023-05-01'): SPECIAL_OPEN_0,
                    pd.Timestamp("2023-05-02"): "Inserted Special Open",
                    pd.Timestamp("2023-06-01"): AD_HOC_SPECIAL_OPEN,
                    pd.Timestamp("2024-05-01"): SPECIAL_OPEN_0,
                }
            )
        )
        .empty
    )

    assert (
        c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-18"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-06-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-09-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-12-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-03-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-06-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-09-14"): "Inserted Quarterly Expiry",
                    # removed: pd.Timestamp('2023-09-15'): QUARTERLY_EXPIRY,
                    pd.Timestamp("2023-12-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-03-15"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-06-21"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-09-20"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2024-12-20"): QUARTERLY_EXPIRY,
                }
            )
        )
        .empty
    )

    assert (
        c.monthly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-02-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-04-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-05-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-07-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-08-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-10-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-11-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-01-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-02-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-04-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-05-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-07-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-08-17"): "Inserted Monthly Expiry",
                    # removed: pd.Timestamp('2023-08-18'): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-10-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2023-11-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-01-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-02-16"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-04-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-05-17"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-07-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-08-16"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-10-18"): MONTHLY_EXPIRY,
                    pd.Timestamp("2024-11-15"): MONTHLY_EXPIRY,
                }
            )
        )
        .empty
    )

    # Verify tags and comments.


@pytest.mark.isolated
def test_test():
    import exchange_calendars_extensions.core as ecx

    ecx.apply_extensions()
    import exchange_calendars as ec

    changes = {
        "add": {
            "2022-01-10": {"type": "holiday", "name": "Holiday"},
            "2022-01-12": {
                "type": "special_open",
                "name": "Special Open",
                "time": "10:00",
            },
            "2022-01-14": {
                "type": "special_close",
                "name": "Special Close",
                "time": "16:00",
            },
            "2022-01-18": {"type": "monthly_expiry", "name": MONTHLY_EXPIRY},
            "2022-01-20": {"type": "quarterly_expiry", "name": QUARTERLY_EXPIRY},
        },
        "remove": [
            "2022-01-11",
            "2022-01-13",
            "2022-01-17",
            "2022-01-19",
            "2022-01-21",
        ],
        "meta": {
            "2022-01-22": {"tags": ["tag1", "tag2"]},
            "2022-01-23": {"comment": "This is a comment"},
            "2022-01-24": {"tags": ["tag3", "tag4"], "comment": "This is a comment"},
        },
    }

    ecx.update_calendar("XLON", changes)

    calendar = ec.get_calendar("XLON")

    assert "2022-01-10" in calendar.holidays_all.holidays()
    assert "2022-01-11" not in calendar.holidays_all.holidays()
    assert "2022-01-12" in calendar.special_opens_all.holidays()
    assert "2022-01-13" not in calendar.special_opens_all.holidays()
    assert "2022-01-14" in calendar.special_closes_all.holidays()
    assert "2022-01-17" not in calendar.special_closes_all.holidays()
    assert "2022-01-18" in calendar.monthly_expiries.holidays()
    assert "2022-01-19" not in calendar.monthly_expiries.holidays()
    assert "2022-01-20" in calendar.quarterly_expiries.holidays()
    assert "2022-01-21" not in calendar.quarterly_expiries.holidays()


@pytest.mark.isolated
def test_quarterly_expiry_rollback_one_day():
    add_test_calendar_and_apply_extensions(
        holidays=[pd.Timestamp("2022-03-18")],
        adhoc_holidays=[],
        regular_special_close=time(14, 00),
        special_closes=[],
        adhoc_special_closes=[],
        regular_special_open=time(11, 00),
        special_opens=[],
        adhoc_special_opens=[],
        weekmask="1111100",
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c = ec.get_calendar("TEST")

    print(type(c))

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert (
        c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp(
                        "2022-03-17"
                    ): QUARTERLY_EXPIRY,  # Should be rolled back from 2022-03-18 since it is a holiday.
                    pd.Timestamp("2022-06-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-09-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-12-16"): QUARTERLY_EXPIRY,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_quarterly_expiry_rollback_multiple_days():
    add_test_calendar_and_apply_extensions(
        holidays=[pd.Timestamp("2022-03-18")],
        adhoc_holidays=[pd.Timestamp("2022-03-17")],
        regular_special_close=time(14, 00),
        special_closes=[(time(14, 00), [pd.Timestamp("2022-03-16")])],
        adhoc_special_closes=[(time(14, 00), [pd.Timestamp("2022-03-15")])],
        regular_special_open=time(11, 00),
        special_opens=[(time(11, 00), [pd.Timestamp("2022-03-14")])],
        adhoc_special_opens=[],
        weekmask="1111100",
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert (
        c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp(
                        "2022-03-11"
                    ): QUARTERLY_EXPIRY,  # Should be rolled back from 2022-03-18.
                    pd.Timestamp("2022-06-17"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-09-16"): QUARTERLY_EXPIRY,
                    pd.Timestamp("2022-12-16"): QUARTERLY_EXPIRY,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_monthly_expiry_rollback_one_day():
    add_test_calendar_and_apply_extensions(
        holidays=[pd.Timestamp("2022-02-18")],
        adhoc_holidays=[],
        regular_special_close=time(14, 00),
        special_closes=[],
        adhoc_special_closes=[],
        regular_special_open=time(11, 00),
        special_opens=[],
        adhoc_special_opens=[],
        weekmask="1111100",
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert (
        c.monthly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-21"): MONTHLY_EXPIRY,
                    pd.Timestamp(
                        "2022-02-17"
                    ): MONTHLY_EXPIRY,  # Should be rolled back from 2022-02-18 since it is a holiday.
                    pd.Timestamp("2022-04-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-05-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-07-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-08-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-10-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-11-18"): MONTHLY_EXPIRY,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_monthly_expiry_rollback_multiple_days():
    add_test_calendar_and_apply_extensions(
        holidays=[pd.Timestamp("2022-02-18")],
        adhoc_holidays=[pd.Timestamp("2022-02-17")],
        regular_special_close=time(14, 00),
        special_closes=[(time(14, 00), [pd.Timestamp("2022-02-16")])],
        adhoc_special_closes=[(time(14, 00), [pd.Timestamp("2022-02-15")])],
        regular_special_open=time(11, 00),
        special_opens=[(time(11, 00), [pd.Timestamp("2022-02-14")])],
        adhoc_special_opens=[],
        weekmask="1111100",
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert (
        c.monthly_expiries.holidays(start=start, end=end, return_name=True)
        .compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-21"): MONTHLY_EXPIRY,
                    pd.Timestamp(
                        "2022-02-11"
                    ): MONTHLY_EXPIRY,  # Should be rolled back from 2022-02-18.
                    pd.Timestamp("2022-04-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-05-20"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-07-15"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-08-19"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-10-21"): MONTHLY_EXPIRY,
                    pd.Timestamp("2022-11-18"): MONTHLY_EXPIRY,
                }
            )
        )
        .empty
    )


@pytest.mark.isolated
def test_set_tags():
    add_test_calendar_and_apply_extensions()

    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.set_tags("TEST", "2023-01-03", ["tag1", "tag2"])

    c = ec.get_calendar("TEST")

    assert c.meta() == {
        pd.Timestamp("2023-01-03"): DayMeta(tags=["tag1", "tag2"], comment=None)
    }

    ecx.set_tags("TEST", "2023-01-03", None)

    c = ec.get_calendar("TEST")

    assert c.meta() == dict()

    ecx.set_tags("TEST", "2023-01-03", [])

    c = ec.get_calendar("TEST")

    assert c.meta() == dict()


@pytest.mark.isolated
def test_set_comment():
    add_test_calendar_and_apply_extensions()

    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.set_comment("TEST", "2023-01-03", "This is a comment")

    c = ec.get_calendar("TEST")

    assert c.meta() == {
        pd.Timestamp("2023-01-03"): DayMeta(tags=[], comment="This is a comment")
    }

    ecx.set_comment("TEST", "2023-01-03", None)

    c = ec.get_calendar("TEST")

    assert c.meta() == dict()

    ecx.set_comment("TEST", "2023-01-03", "")

    c = ec.get_calendar("TEST")

    assert c.meta() == dict()


@pytest.mark.isolated
def test_set_meta():
    add_test_calendar_and_apply_extensions()

    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.set_meta("TEST", "2023-01-03", {"comment": "This is a comment"})
    ecx.set_meta("TEST", "2023-01-04", {"tags": ["tag1", "tag2"]})
    ecx.set_meta(
        "TEST", "2023-01-05", {"tags": ["tag1", "tag2"], "comment": "This is a comment"}
    )
    ecx.set_meta("TEST", "2023-01-06", None)

    c = ec.get_calendar("TEST")

    assert c.meta() == {
        pd.Timestamp("2023-01-03"): DayMeta(tags=[], comment="This is a comment"),
        pd.Timestamp("2023-01-04"): DayMeta(tags=["tag1", "tag2"], comment=None),
        pd.Timestamp("2023-01-05"): DayMeta(
            tags=["tag1", "tag2"], comment="This is a comment"
        ),
    }

    ecx.set_meta("TEST", "2023-01-03", None)
    ecx.set_meta("TEST", "2023-01-04", None)
    ecx.set_meta("TEST", "2023-01-05", None)

    c = ec.get_calendar("TEST")

    assert c.meta() == dict()


@pytest.mark.isolated
def test_get_meta():
    add_test_calendar_and_apply_extensions()

    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    ecx.set_meta("TEST", "2023-01-03", {"comment": "This is a comment"})
    ecx.set_meta("TEST", "2023-01-04", {"tags": ["tag1", "tag2"]})
    ecx.set_meta(
        "TEST", "2023-01-05", {"tags": ["tag1", "tag2"], "comment": "This is a comment"}
    )

    c = ec.get_calendar("TEST")

    assert c.meta() == {
        pd.Timestamp("2023-01-03"): DayMeta(tags=[], comment="This is a comment"),
        pd.Timestamp("2023-01-04"): DayMeta(tags=["tag1", "tag2"], comment=None),
        pd.Timestamp("2023-01-05"): DayMeta(
            tags=["tag1", "tag2"], comment="This is a comment"
        ),
    }


@pytest.mark.isolated
def test_get_meta_tz_naive():
    add_test_calendar_and_apply_extensions()

    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    day_1 = pd.Timestamp("2023-01-03")
    day_2 = day_1 + pd.Timedelta(days=1)
    day_3 = day_2 + pd.Timedelta(days=1)

    meta_1 = DayMeta(tags=[], comment="This is a comment")
    meta_2 = DayMeta(tags=["tag1", "tag2"], comment=None)
    meta_3 = DayMeta(tags=["tag1", "tag2"], comment="This is a comment")

    ecx.set_meta("TEST", day_1, meta_1)
    ecx.set_meta("TEST", day_2, meta_2)
    ecx.set_meta("TEST", day_3, meta_3)

    c = ec.get_calendar("TEST")

    # Test combinations of start and end aligned with date boundary.

    # start
    assert c.meta(start=day_1 - pd.Timedelta(days=1)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(start=day_1) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(start=day_2) == OrderedDict([(day_2, meta_2), (day_3, meta_3)])
    assert c.meta(start=day_3) == OrderedDict([(day_3, meta_3)])
    assert c.meta(start=day_3 + pd.Timedelta(days=1)) == OrderedDict()

    # end
    assert c.meta(end=day_3 + pd.Timedelta(days=1)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(end=day_3) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(end=day_2) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(end=day_1) == OrderedDict([(day_1, meta_1)])
    assert c.meta(end=day_1 - pd.Timedelta(days=1)) == OrderedDict()

    # start & end
    assert c.meta(start=day_1, end=day_3) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(start=day_2, end=day_2) == OrderedDict([(day_2, meta_2)])

    # Test combinations of start and end not aligned with date boundary.

    # start
    assert c.meta(start=day_1 - pd.Timedelta(hours=1)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(start=day_1 + pd.Timedelta(hours=1)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(
        start=day_1
        + pd.Timedelta(
            hours=23,
            minutes=59,
            seconds=59,
            milliseconds=999,
            microseconds=999,
            nanoseconds=999,
        )
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)])
    assert c.meta(
        start=day_1 + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)])
    assert c.meta(start=day_1 + pd.Timedelta(hours=24)) == OrderedDict(
        [(day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(start=day_1 + pd.Timedelta(days=1)) == OrderedDict(
        [(day_2, meta_2), (day_3, meta_3)]
    )

    # end
    assert c.meta(end=day_3 + pd.Timedelta(hours=24)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(end=day_3 + pd.Timedelta(days=1)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(
        end=day_3 + pd.Timedelta(hours=1) - pd.Timedelta(nanoseconds=1)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)])
    assert c.meta(end=day_3 + pd.Timedelta(nanoseconds=1)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(end=day_3) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2), (day_3, meta_3)]
    )
    assert c.meta(end=day_3 - pd.Timedelta(nanoseconds=1)) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2)]
    )


def test_get_meta_tz_aware():
    add_test_calendar_and_apply_extensions()

    import exchange_calendars as ec
    import exchange_calendars_extensions.core as ecx

    day_1 = pd.Timestamp("2024-03-31")  # Begin of DST 02:00 -> 03:00
    day_2 = pd.Timestamp("2024-09-29")  # End of DST 03:00 -> 02:00

    meta_1 = DayMeta(tags=["tag1", "tag2"], comment="This is a comment")
    meta_2 = DayMeta(tags=["tag1", "tag2"], comment="This is a comment")

    ecx.set_meta("TEST", day_1, meta_1)
    ecx.set_meta("TEST", day_2, meta_2)

    c = ec.get_calendar("TEST")

    assert c.tz == timezone("CET")

    assert c.meta() == OrderedDict([(day_1, meta_1), (day_2, meta_2)])

    # Test combinations of timezone-aware start and end.

    # start
    # day_1 only has 23 hours due to DST transition

    # start in timezone CET, same as the calendar
    assert c.meta(start=day_1.tz_localize(tz="CET")) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2)]
    )
    assert c.meta(
        start=day_1.tz_localize(tz="CET")
        + pd.Timedelta(days=1)
        - pd.Timedelta(hours=1, nanoseconds=1)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        start=day_1.tz_localize(tz="CET")
        + pd.Timedelta(
            hours=22,
            minutes=59,
            seconds=59,
            milliseconds=999,
            microseconds=999,
            nanoseconds=999,
        )
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        start=day_1.tz_localize(tz="CET") + pd.Timedelta(days=1) - pd.Timedelta(hours=1)
    ) == OrderedDict([(day_2, meta_2)])
    assert c.meta(
        start=day_1.tz_localize(tz="CET") + pd.Timedelta(hours=23)
    ) == OrderedDict([(day_2, meta_2)])

    # start in UTC
    assert c.meta(
        start=day_1.tz_localize(tz="CET").tz_convert(tz="UTC")
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        start=day_1.tz_localize(tz="CET").tz_convert(tz="UTC")
        + pd.Timedelta(days=1)
        - pd.Timedelta(hours=1, nanoseconds=1)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        start=day_1.tz_localize(tz="CET").tz_convert(tz="UTC")
        + pd.Timedelta(
            hours=22,
            minutes=59,
            seconds=59,
            milliseconds=999,
            microseconds=999,
            nanoseconds=999,
        )
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        start=day_1.tz_localize(tz="CET").tz_convert(tz="UTC")
        + pd.Timedelta(days=1)
        - pd.Timedelta(hours=1)
    ) == OrderedDict([(day_2, meta_2)])
    assert c.meta(
        start=day_1.tz_localize(tz="CET").tz_convert(tz="UTC") + pd.Timedelta(hours=23)
    ) == OrderedDict([(day_2, meta_2)])

    # end
    # day_2 has 25 hours due to DST transition

    # end in timezone CET, same as the calendar
    assert c.meta(
        end=day_2.tz_localize(tz="CET") + pd.Timedelta(hours=25)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        end=day_2.tz_localize(tz="CET")
        + pd.Timedelta(
            hours=24,
            minutes=59,
            seconds=59,
            milliseconds=999,
            microseconds=999,
            nanoseconds=999,
        )
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        end=day_2.tz_localize(tz="CET")
        + pd.Timedelta(days=1)
        + pd.Timedelta(hours=1, nanoseconds=-1)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(end=day_2.tz_localize(tz="CET")) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2)]
    )
    assert c.meta(
        end=day_2.tz_localize(tz="CET") - pd.Timedelta(nanoseconds=1)
    ) == OrderedDict([(day_1, meta_1)])

    # end in UTC
    assert c.meta(
        end=day_2.tz_localize(tz="CET").tz_convert(tz="UTC") + pd.Timedelta(hours=25)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        end=day_2.tz_localize(tz="CET").tz_convert(tz="UTC")
        + pd.Timedelta(
            hours=24,
            minutes=59,
            seconds=59,
            milliseconds=999,
            microseconds=999,
            nanoseconds=999,
        )
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(
        end=day_2.tz_localize(tz="CET").tz_convert(tz="UTC")
        + pd.Timedelta(days=1)
        + pd.Timedelta(hours=1, nanoseconds=-1)
    ) == OrderedDict([(day_1, meta_1), (day_2, meta_2)])
    assert c.meta(end=day_2.tz_localize(tz="CET").tz_convert(tz="UTC")) == OrderedDict(
        [(day_1, meta_1), (day_2, meta_2)]
    )
    assert c.meta(
        end=day_2.tz_localize(tz="CET").tz_convert(tz="UTC")
        - pd.Timedelta(nanoseconds=1)
    ) == OrderedDict([(day_1, meta_1)])
