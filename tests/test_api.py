import datetime as dt
import importlib.metadata
from typing import Any, Literal, cast

import exchange_calendars as ec
import pandas as pd
import pytest
from exchange_calendars.exchange_calendar import HolidayCalendar
from pydantic.experimental.missing_sentinel import MISSING

import exchange_calendars_extensions.core as ecx
from exchange_calendars_extensions.core import ExtendedExchangeCalendar
from exchange_calendars_extensions.core.changes import (
    BusinessDaySpec,
    DayChange,
    NonBusinessDaySpec,
)
from exchange_calendars_extensions.core.datetime import DateLike
from tests.synthetic_calendar import (
    CLOSE_REGULAR,
    CLOSE_SPECIAL_AD_HOC,
    CLOSE_SPECIAL_CUSTOM,
    CLOSE_SPECIAL_REGULAR,
    HOLIDAY_ADHOC_DT,
    HOLIDAY_REGULAR_DT,
    HOLIDAY_REGULAR_NAME,
    OPEN_REGULAR,
    OPEN_SPECIAL_AD_HOC,
    OPEN_SPECIAL_CUSTOM,
    OPEN_SPECIAL_REGULAR,
    REGULAR_DAY_DT,
    SPECIAL_CLOSE_ADHOC_DT,
    SPECIAL_CLOSE_REGULAR_DT,
    SPECIAL_CLOSE_REGULAR_NAME,
    SPECIAL_OPEN_ADHOC_DT,
    SPECIAL_OPEN_REGULAR_DT,
    SPECIAL_OPEN_REGULAR_NAME,
    WEEKEND_DAY_DT,
    add_extended_calendar_class,
    create_test_calendar_class,
)

_EC_VERSION: tuple[int, ...] = tuple(
    int(x) for x in importlib.metadata.version("exchange-calendars").split(".")
)
_EC_VERSION_THRESHOLD: tuple[int, ...] = ()  # (4, 13, 2) ?

# Skip some tests until https://github.com/gerrymanoim/exchange_calendars/pull/553 is resolved.
_skip_below_threshold = pytest.mark.skipif(
    not _EC_VERSION_THRESHOLD or _EC_VERSION <= _EC_VERSION_THRESHOLD,
    reason=f"requires exchange-calendars >= {'.'.join(str(x) for x in _EC_VERSION_THRESHOLD)}",
)

MODIFIED_DAY_NAME = "Modified day"


@pytest.mark.isolated
def test_unmodified_calendars():
    """Test that calendars are unmodified when the module is just imported, without calling apply_extensions()"""
    c = ec.get_calendar("XETR")

    # Check if returned Calendar is of expected type.
    assert isinstance(c, ec.ExchangeCalendar)

    # Check if returned Calendar is not of extended type.
    assert not isinstance(c, ecx.ExtendedExchangeCalendar)
    assert not isinstance(c, ecx.ExchangeCalendarExtensions)


@pytest.mark.isolated
def test_apply_extensions():
    """Test that calendars are modified when apply_extensions() is called"""
    ecx.apply_extensions()

    c = ec.get_calendar("XETR")

    # Check if returned Calendar is of expected types.
    assert isinstance(c, ec.ExchangeCalendar)
    assert isinstance(c, ecx.ExtendedExchangeCalendar)
    assert isinstance(c, ecx.ExchangeCalendarExtensions)


@pytest.mark.isolated
def test_extended_calendar_xetr():
    """Test the additional properties of the extended XETR calendar."""
    ecx.apply_extensions()

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


# @pytest.mark.isolated
def test_extended_calendar_test(test_calendar):
    # add_test_calendar()

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Verify regular holidays for 2022, 2023, and 2024.
    assert c.regular_holidays is not None
    s = c.regular_holidays.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    HOLIDAY_REGULAR_DT + pd.DateOffset(years=-1): HOLIDAY_REGULAR_NAME,
                    HOLIDAY_REGULAR_DT: HOLIDAY_REGULAR_NAME,
                    HOLIDAY_REGULAR_DT + pd.DateOffset(years=1): HOLIDAY_REGULAR_NAME,
                }
            )
        ).empty
    )

    # Verify adhoc holidays.
    assert c.adhoc_holidays == [HOLIDAY_ADHOC_DT]

    # Verify special closes for 2022, 2023, and 2024.
    assert len(c.special_closes) == 1
    assert len(c.special_closes[0]) == 2
    assert c.special_closes[0][0] == CLOSE_SPECIAL_REGULAR
    assert isinstance(c.special_closes[0][1], HolidayCalendar)
    s = c.special_closes[0][1].holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    SPECIAL_CLOSE_REGULAR_DT
                    + pd.DateOffset(years=-1): SPECIAL_CLOSE_REGULAR_NAME,
                    SPECIAL_CLOSE_REGULAR_DT: SPECIAL_CLOSE_REGULAR_NAME,
                    SPECIAL_CLOSE_REGULAR_DT
                    + pd.DateOffset(years=1): SPECIAL_CLOSE_REGULAR_NAME,
                }
            )
        ).empty
    )

    # Verify adhoc special closes.
    assert c.special_closes_adhoc == [
        (CLOSE_SPECIAL_AD_HOC, pd.DatetimeIndex([SPECIAL_CLOSE_ADHOC_DT]))
    ]

    # Verify special opens for 2022, 2023, and 2024.
    assert len(c.special_opens) == 1
    assert len(c.special_opens[0]) == 2
    assert c.special_opens[0][0] == OPEN_SPECIAL_REGULAR
    assert isinstance(c.special_opens[0][1], HolidayCalendar)
    s = c.special_opens[0][1].holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    SPECIAL_OPEN_REGULAR_DT
                    + pd.DateOffset(years=-1): SPECIAL_OPEN_REGULAR_NAME,
                    SPECIAL_OPEN_REGULAR_DT: SPECIAL_OPEN_REGULAR_NAME,
                    SPECIAL_OPEN_REGULAR_DT
                    + pd.DateOffset(years=1): SPECIAL_OPEN_REGULAR_NAME,
                }
            )
        ).empty
    )

    # Verify adhoc special opens.
    assert c.special_opens_adhoc == [
        (OPEN_SPECIAL_AD_HOC, pd.DatetimeIndex([pd.Timestamp("2023-06-01")]))
    ]

    # Verify additional holiday calendars.

    s = c.holidays_all.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    HOLIDAY_REGULAR_DT + pd.DateOffset(years=-1): HOLIDAY_REGULAR_NAME,
                    HOLIDAY_REGULAR_DT: HOLIDAY_REGULAR_NAME,
                    HOLIDAY_ADHOC_DT: None,
                    HOLIDAY_REGULAR_DT + pd.DateOffset(years=1): HOLIDAY_REGULAR_NAME,
                }
            )
        ).empty
    )

    s = c.special_closes_all.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    SPECIAL_CLOSE_REGULAR_DT
                    + pd.DateOffset(years=-1): SPECIAL_CLOSE_REGULAR_NAME,
                    SPECIAL_CLOSE_REGULAR_DT: SPECIAL_CLOSE_REGULAR_NAME,
                    SPECIAL_CLOSE_ADHOC_DT: None,
                    SPECIAL_CLOSE_REGULAR_DT
                    + pd.DateOffset(years=1): SPECIAL_CLOSE_REGULAR_NAME,
                }
            )
        ).empty
    )

    s = c.special_opens_all.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    SPECIAL_OPEN_REGULAR_DT
                    + pd.DateOffset(years=-1): SPECIAL_OPEN_REGULAR_NAME,
                    SPECIAL_OPEN_REGULAR_DT: SPECIAL_OPEN_REGULAR_NAME,
                    SPECIAL_OPEN_ADHOC_DT: None,
                    SPECIAL_OPEN_REGULAR_DT
                    + pd.DateOffset(years=1): SPECIAL_OPEN_REGULAR_NAME,
                }
            )
        ).empty
    )

    s = c.weekend_days.holidays(
        start=pd.Timestamp("2023-01-01"),
        end=pd.Timestamp("2023-01-31"),
        return_name=True,
    )
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    pd.Timestamp("2023-01-01"): None,
                    pd.Timestamp("2023-01-07"): None,
                    pd.Timestamp("2023-01-08"): None,
                    pd.Timestamp("2023-01-14"): None,
                    pd.Timestamp("2023-01-15"): None,
                    pd.Timestamp("2023-01-21"): None,
                    pd.Timestamp("2023-01-22"): None,
                    pd.Timestamp("2023-01-28"): None,
                    pd.Timestamp("2023-01-29"): None,
                }
            )
        ).empty
    )

    assert c.quarterly_expiries is not None
    s = c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    pd.Timestamp("2022-03-18"): None,
                    pd.Timestamp("2022-06-17"): None,
                    pd.Timestamp("2022-09-16"): None,
                    pd.Timestamp("2022-12-16"): None,
                    pd.Timestamp("2023-03-17"): None,
                    pd.Timestamp("2023-06-16"): None,
                    pd.Timestamp("2023-09-15"): None,
                    pd.Timestamp("2023-12-15"): None,
                    pd.Timestamp("2024-03-15"): None,
                    pd.Timestamp("2024-06-21"): None,
                    pd.Timestamp("2024-09-20"): None,
                    pd.Timestamp("2024-12-20"): None,
                }
            )
        ).empty
    )

    assert c.monthly_expiries is not None
    s = c.monthly_expiries.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-21"): None,
                    pd.Timestamp("2022-02-18"): None,
                    pd.Timestamp("2022-04-15"): None,
                    pd.Timestamp("2022-05-20"): None,
                    pd.Timestamp("2022-07-15"): None,
                    pd.Timestamp("2022-08-19"): None,
                    pd.Timestamp("2022-10-21"): None,
                    pd.Timestamp("2022-11-18"): None,
                    pd.Timestamp("2023-01-20"): None,
                    pd.Timestamp("2023-02-17"): None,
                    pd.Timestamp("2023-04-21"): None,
                    pd.Timestamp("2023-05-19"): None,
                    pd.Timestamp("2023-07-21"): None,
                    pd.Timestamp("2023-08-18"): None,
                    pd.Timestamp("2023-10-20"): None,
                    pd.Timestamp("2023-11-17"): None,
                    pd.Timestamp("2024-01-19"): None,
                    pd.Timestamp("2024-02-16"): None,
                    pd.Timestamp("2024-04-19"): None,
                    pd.Timestamp("2024-05-17"): None,
                    pd.Timestamp("2024-07-19"): None,
                    pd.Timestamp("2024-08-16"): None,
                    pd.Timestamp("2024-10-18"): None,
                    pd.Timestamp("2024-11-15"): None,
                }
            )
        ).empty
    )

    s = c.last_trading_days_of_months.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-31"): None,
                    pd.Timestamp("2022-02-28"): None,
                    pd.Timestamp("2022-03-31"): None,
                    pd.Timestamp("2022-04-29"): None,
                    pd.Timestamp("2022-05-31"): None,
                    pd.Timestamp("2022-06-30"): None,
                    pd.Timestamp("2022-07-29"): None,
                    pd.Timestamp("2022-08-31"): None,
                    pd.Timestamp("2022-09-30"): None,
                    pd.Timestamp("2022-10-31"): None,
                    pd.Timestamp("2022-11-30"): None,
                    pd.Timestamp("2022-12-30"): None,
                    pd.Timestamp("2023-01-31"): None,
                    pd.Timestamp("2023-02-28"): None,
                    pd.Timestamp("2023-03-31"): None,
                    pd.Timestamp("2023-04-28"): None,
                    pd.Timestamp("2023-05-31"): None,
                    pd.Timestamp("2023-06-30"): None,
                    pd.Timestamp("2023-07-31"): None,
                    pd.Timestamp("2023-08-31"): None,
                    pd.Timestamp("2023-09-29"): None,
                    pd.Timestamp("2023-10-31"): None,
                    pd.Timestamp("2023-11-30"): None,
                    pd.Timestamp("2023-12-29"): None,
                    pd.Timestamp("2024-01-31"): None,
                    pd.Timestamp("2024-02-29"): None,
                    pd.Timestamp("2024-03-29"): None,
                    pd.Timestamp("2024-04-30"): None,
                    pd.Timestamp("2024-05-31"): None,
                    pd.Timestamp("2024-06-28"): None,
                    pd.Timestamp("2024-07-31"): None,
                    pd.Timestamp("2024-08-30"): None,
                    pd.Timestamp("2024-09-30"): None,
                    pd.Timestamp("2024-10-31"): None,
                    pd.Timestamp("2024-11-29"): None,
                    pd.Timestamp("2024-12-31"): None,
                }
            )
        ).empty
    )

    s = c.last_regular_trading_days_of_months.holidays(
        start=start, end=end, return_name=True
    )
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-31"): None,
                    pd.Timestamp("2022-02-28"): None,
                    pd.Timestamp("2022-03-31"): None,
                    pd.Timestamp("2022-04-29"): None,
                    pd.Timestamp("2022-05-31"): None,
                    pd.Timestamp("2022-06-30"): None,
                    pd.Timestamp("2022-07-29"): None,
                    pd.Timestamp("2022-08-31"): None,
                    pd.Timestamp("2022-09-30"): None,
                    pd.Timestamp("2022-10-31"): None,
                    pd.Timestamp("2022-11-30"): None,
                    pd.Timestamp("2022-12-30"): None,
                    pd.Timestamp("2023-01-31"): None,
                    pd.Timestamp("2023-02-28"): None,
                    pd.Timestamp("2023-03-31"): None,
                    pd.Timestamp("2023-04-28"): None,
                    pd.Timestamp("2023-05-31"): None,
                    pd.Timestamp("2023-06-30"): None,
                    pd.Timestamp("2023-07-31"): None,
                    pd.Timestamp("2023-08-31"): None,
                    pd.Timestamp("2023-09-29"): None,
                    pd.Timestamp("2023-10-31"): None,
                    pd.Timestamp("2023-11-30"): None,
                    pd.Timestamp("2023-12-29"): None,
                    pd.Timestamp("2024-01-31"): None,
                    pd.Timestamp("2024-02-29"): None,
                    pd.Timestamp("2024-03-29"): None,
                    pd.Timestamp("2024-04-30"): None,
                    pd.Timestamp("2024-05-31"): None,
                    pd.Timestamp("2024-06-28"): None,
                    pd.Timestamp("2024-07-31"): None,
                    pd.Timestamp("2024-08-30"): None,
                    pd.Timestamp("2024-09-30"): None,
                    pd.Timestamp("2024-10-31"): None,
                    pd.Timestamp("2024-11-29"): None,
                    pd.Timestamp("2024-12-31"): None,
                }
            )
        ).empty
    )


SpecialSessionType = Literal["special open", "special close"]


def assert_not_in_special_sessions(
    date: DateLike,
    c: ExtendedExchangeCalendar,
    session_type: SpecialSessionType,
):
    if session_type == "special open":
        attr_regular = c.special_opens
        attr_adhoc = c.special_opens_adhoc
        attr_all = c.special_opens_all
    elif session_type == "special close":
        attr_regular = c.special_closes
        attr_adhoc = c.special_closes_adhoc
        attr_all = c.special_closes_all
    else:
        raise ValueError(f"session_type {session_type} not supported")
    for t, cal in attr_regular:
        if isinstance(cal, HolidayCalendar):
            assert cal.holidays(start=date, end=date, return_name=True).empty
        elif isinstance(cal, int):
            assert date.dayofweek != cal
    for t, idx in attr_adhoc:
        assert date not in idx
    assert attr_all.holidays(start=date, end=date, return_name=True).empty


def assert_in_regular_special_days(
    c: ExtendedExchangeCalendar,
    date: DateLike,
    time: dt.time,
    name: str | None,
    session_type: SpecialSessionType,
) -> None:
    # Get the special days (regular special opens or closes).
    special_days = (
        c.special_opens if session_type == "special open" else c.special_closes
    )

    # Time appears is in special days.
    assert time in [t for t, cal in special_days]

    # Check if day appears in the correct calendar for the given time, and only there.
    for t, cal in special_days:
        assert isinstance(cal, HolidayCalendar)
        if t == time:
            # Day should be in this calendar.
            s = cal.holidays(start=date, end=date, return_name=True)
            assert isinstance(s, pd.Series) and (
                s.compare(
                    pd.Series(
                        {
                            date: name,
                        }
                    )
                ).empty
            )
        else:
            # Day should not be in this calendar.
            assert cal.holidays(start=date, end=date, return_name=True).empty


def assert_series_equal(s: Any, data: dict):
    assert isinstance(s, pd.Series) and s.compare(pd.Series(data)).empty


@pytest.mark.parametrize("weekend_day", [False, True, MISSING])
@pytest.mark.parametrize("set_name", ["set", "inherit", "none"])
@pytest.mark.parametrize(
    "date,name_orig,name,weekend_day_orig",
    [
        (
            REGULAR_DAY_DT,
            None,
            MODIFIED_DAY_NAME,
            False,
        ),  # Turn a regular business day into a holiday/weekend day.
        (
            WEEKEND_DAY_DT,
            None,
            MODIFIED_DAY_NAME,
            True,
        ),  # Turn a regular weekend day into a holiday/weekend day.
        (
            HOLIDAY_REGULAR_DT,
            HOLIDAY_REGULAR_NAME,
            MODIFIED_DAY_NAME,
            False,
        ),  # Turn a regular holiday into a holiday/weekend day.
        (
            HOLIDAY_ADHOC_DT,
            None,
            MODIFIED_DAY_NAME,
            False,
        ),  # Turn an ad-hoc special close day into a holiday/weekend day.
        (
            SPECIAL_CLOSE_REGULAR_DT,
            SPECIAL_CLOSE_REGULAR_NAME,
            MODIFIED_DAY_NAME,
            False,
        ),  # Turn a regular special close day into a holiday/weekend day.
        (
            SPECIAL_CLOSE_ADHOC_DT,
            None,
            MODIFIED_DAY_NAME,
            False,
        ),  # Turn an ad-hoc special close day into a holiday/weekend day.
        (
            SPECIAL_OPEN_REGULAR_DT,
            SPECIAL_OPEN_REGULAR_NAME,
            MODIFIED_DAY_NAME,
            False,
        ),  # Turn a regular special open day into a holiday/weekend day.
        (
            SPECIAL_OPEN_ADHOC_DT,
            None,
            MODIFIED_DAY_NAME,
            False,
        ),  # Turn an ad-hoc special open day into a holiday/weekend day.
    ],
)
def test_set_holiday(
    date: DateLike,
    name_orig: str | None,
    weekend_day_orig: bool,
    name: str,
    weekend_day: bool | MISSING,
    set_name: Literal["set", "inherit", "none"],
    test_calendar,
):
    def get_assigned_and_expected_name() -> tuple[str | None | MISSING, str | None]:
        if set_name == "set":
            return name, name
        elif set_name == "none":
            return None, None
        else:
            return MISSING, name_orig

    assigned_name, expected_name = get_assigned_and_expected_name()

    ecx.change_day(
        exchange="TEST",
        date=date,
        action=DayChange(
            spec=NonBusinessDaySpec(weekend_day=weekend_day, holiday=True),
            name=assigned_name,
        ),
    )

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    # Holiday should be in regular holidays.
    assert c.regular_holidays is not None
    s = c.regular_holidays.holidays(start=date, end=date, return_name=True)
    assert_series_equal(s, {date: expected_name})

    # Holiday should not be in ad-hoc holidays.
    assert date not in c.adhoc_holidays

    # Holiday should be in combined holidays calendar.
    s = c.holidays_all.holidays(start=date, end=date, return_name=True)
    assert_series_equal(s, {date: expected_name})

    # Holiday should not be in special opens or closes.
    assert_not_in_special_sessions(date, c, "special open")
    assert_not_in_special_sessions(date, c, "special close")

    # Holiday should not be in quarterly or monthly expiry days, if defined.
    if c.monthly_expiries:
        assert c.monthly_expiries.holidays(start=date, end=date, return_name=True).empty
    if c.quarterly_expiries:
        assert c.quarterly_expiries.holidays(
            start=date, end=date, return_name=True
        ).empty

    # Holiday should not be in last (regular) trading day of month calendar.
    assert c.last_trading_days_of_months.holidays(
        start=date, end=date, return_name=True
    ).empty
    assert c.last_regular_trading_days_of_months.holidays(
        start=date, end=date, return_name=True
    ).empty

    if weekend_day is MISSING and weekend_day_orig or weekend_day is True:
        s = c.weekend_days.holidays(start=date, end=date, return_name=True)
        assert_series_equal(s, {date: None})
        assert c.week_days.holidays(start=date, end=date, return_name=True).empty
    else:
        assert c.weekend_days.holidays(start=date, end=date, return_name=True).empty
        s = c.week_days.holidays(start=date, end=date, return_name=True)
        assert_series_equal(s, {date: None})

    # Check if custom business day rolls over day.
    assert date < c.day.rollforward(date)


@pytest.mark.parametrize(
    "holiday",
    [
        False,
        MISSING,
    ],
)
@pytest.mark.parametrize(
    "set_name",
    [
        "inherit",
        "none",
    ],
)
@pytest.mark.parametrize(
    "date,name_orig,regular_holiday_orig,ad_hoc_holiday_orig",
    [
        (REGULAR_DAY_DT, None, False, False),  # Regular business day.
        (WEEKEND_DAY_DT, None, False, False),  # Regular weekend day.
        (HOLIDAY_REGULAR_DT, HOLIDAY_REGULAR_NAME, True, False),  # Regular holiday.
        (HOLIDAY_ADHOC_DT, None, False, True),  # Ad-hoc holiday.
        (
            SPECIAL_CLOSE_REGULAR_DT,
            SPECIAL_CLOSE_REGULAR_NAME,
            False,
            False,
        ),  # Regular special close day.
        (SPECIAL_CLOSE_ADHOC_DT, None, False, False),  # Ad-hoc special close day.
        (
            SPECIAL_OPEN_REGULAR_DT,
            SPECIAL_OPEN_REGULAR_NAME,
            False,
            False,
        ),  # Regular special open day.
        (SPECIAL_OPEN_ADHOC_DT, None, False, False),  # Ad-hoc special open day.
    ],
)
def test_set_weekend_day(
    date: DateLike,
    name_orig: str | None,
    regular_holiday_orig: bool,
    ad_hoc_holiday_orig: bool,
    holiday: Literal[False] | MISSING,
    set_name: Literal["inherit", "none"],
    test_calendar,
):
    ecx.change_day(
        exchange="TEST",
        date=date,
        action=DayChange(
            spec=NonBusinessDaySpec(weekend_day=True, holiday=holiday),
            name=(None if set_name == "none" else MISSING),
        ),
    )

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    # Expected name of the new holiday.
    expected_name = None if set_name == "none" else name_orig

    if holiday is MISSING and regular_holiday_orig:
        assert c.regular_holidays is not None
        s = c.regular_holidays.holidays(start=date, end=date, return_name=True)
        # Day should be in regular holidays.
        assert_series_equal(s, {date: expected_name})
    else:
        assert (
            c.regular_holidays is not None
            and c.regular_holidays.holidays(
                start=date, end=date, return_name=True
            ).empty
        )

    assert (holiday is MISSING and ad_hoc_holiday_orig) ^ (date not in c.adhoc_holidays)

    if holiday is MISSING and (regular_holiday_orig or ad_hoc_holiday_orig):
        # Day should be in combined holidays calendar.
        s = c.holidays_all.holidays(start=date, end=date, return_name=True)
        assert_series_equal(s, {date: None if ad_hoc_holiday_orig else expected_name})
    else:
        assert c.holidays_all.holidays(start=date, end=date, return_name=True).empty

    # Day should not be in special opens or closes.
    assert_not_in_special_sessions(date, c, "special open")
    assert_not_in_special_sessions(date, c, "special close")

    # Day should not be in quarterly or monthly expiry days, if defined.
    if c.monthly_expiries:
        assert c.monthly_expiries.holidays(start=date, end=date, return_name=True).empty
    if c.quarterly_expiries:
        assert c.quarterly_expiries.holidays(
            start=date, end=date, return_name=True
        ).empty

    # Holiday should not be in last (regular) trading day of month calendar.
    assert c.last_trading_days_of_months.holidays(
        start=date, end=date, return_name=True
    ).empty
    assert c.last_regular_trading_days_of_months.holidays(
        start=date, end=date, return_name=True
    ).empty

    # Day should be in weekend days, but not in week days.
    s = c.weekend_days.holidays(start=date, end=date, return_name=True)
    assert_series_equal(s, {date: None})
    assert c.week_days.holidays(start=date, end=date, return_name=True).empty

    # Check if custom business day rolls over day.
    assert date < c.day.rollforward(date)


def check_regular_special_session(
    session_type: SpecialSessionType,
    calendar: ExtendedExchangeCalendar,
    date: DateLike,
) -> tuple[Literal["regular", "adhoc", "normal"], dt.time, str | None]:
    prop_regular = (
        calendar.special_opens
        if session_type == "special open"
        else calendar.special_closes
    )
    prop_ahhoc = (
        calendar.special_opens_adhoc
        if session_type == "special open"
        else calendar.special_closes_adhoc
    )
    assert isinstance(prop_regular, list)
    assert all(
        isinstance(item, tuple)
        and len(item) == 2
        and isinstance(item[0], dt.time)
        and isinstance(item[1], HolidayCalendar)
        for item in prop_regular
    )

    # Tuple containing the time and name pairs of any special sessions that match the date. If non-empty, this
    # should contain exactly one element.
    sessions_regular = tuple(
        (t, cal.holidays(start=date, end=date, return_name=True).iloc[0])
        for t, cal in prop_regular
        if not cal.holidays(start=date, end=date, return_name=True).empty
    )

    assert len(sessions_regular) <= 1

    sessions_adhoc = tuple(t for t, dates in prop_ahhoc if date in dates)

    assert len(sessions_adhoc) <= 1

    assert len(sessions_regular) + len(sessions_adhoc) <= 1

    if len(sessions_regular) > 0:
        return "regular", sessions_regular[0][0], sessions_regular[0][1]
    elif len(sessions_adhoc) > 0:
        return "adhoc", sessions_adhoc[0], None
    return (
        "normal",
        OPEN_REGULAR if session_type == "special open" else CLOSE_REGULAR,
        None,
    )


def get_assigned_and_expected_name(
    set_name: Literal["set", "none", "inherit"], name: str, name_orig: str | None
) -> tuple[str | None | MISSING, str | None]:
    if set_name == "set":
        return name, name
    elif set_name == "none":
        return None, None
    else:
        return MISSING, name_orig


def assert_in_special_sessions(
    *,
    session_type: SpecialSessionType,
    calendar: ExtendedExchangeCalendar,
    date: DateLike,
    name_orig: str | None,
    assigned_name: str | None | MISSING,
    expected_name: str | None,
    expected_time: dt.time,
    orig: tuple[Literal["regular", "adhoc", "normal"], dt.time, str | None],
):
    prop_adhoc = (
        calendar.special_opens_adhoc
        if session_type == "special open"
        else calendar.special_closes_adhoc
    )
    if (
        orig[0] == "regular"
        and orig[1] == expected_time
        and (assigned_name is MISSING or assigned_name == orig[2])
    ):
        # Day should be in regular special sessions with expected open/close time.
        assert_in_regular_special_days(
            calendar, date, expected_time, name_orig, session_type
        )
    elif (
        orig[0] == "adhoc"
        and orig[1] == expected_time
        and (assigned_name is MISSING or assigned_name is None)
    ):
        # Day should be in ad-hoc special opens with expected open time.
        entry = [(t, dates) for t, dates in prop_adhoc if t == expected_time]
        assert len(entry) == 1
        _, dates = entry[0]
        assert date in dates
    else:
        # Day should be in regular special opens with expected open time.
        assert_in_regular_special_days(
            calendar, date, expected_time, expected_name, session_type
        )


def assert_not_in_holidays(calendar: ExtendedExchangeCalendar, date: DateLike) -> None:
    # Day should not be in regular holidays.
    assert (
        calendar.regular_holidays is not None
        and calendar.regular_holidays.holidays(
            start=date, end=date, return_name=True
        ).empty
    )

    # Day should not be in ad-hoc holidays.
    assert date not in calendar.adhoc_holidays

    # Day should not be in combined holidays calendar.
    assert calendar.holidays_all.holidays(start=date, end=date, return_name=True).empty


def get_expected_session_time(
    side: Literal["open", "close"],
    assigned_time: dt.time | Literal["regular"] | MISSING,
    original_time: dt.time,
) -> dt.time:
    if assigned_time is MISSING:
        return original_time
    elif assigned_time == "regular":
        return OPEN_REGULAR if side == "open" else CLOSE_REGULAR
    else:
        return assigned_time


def _make_param_test_set_business_day(
    date: dt.date, name_orig: str | None, type_orig: str, marks=()
) -> tuple:
    label = f"day_type_orig={type_orig}"
    return pytest.param(date, name_orig, type_orig, id=label, marks=marks)


@pytest.mark.parametrize(
    "close",
    [
        pytest.param(MISSING, id="close=inherit"),
        pytest.param("regular", id="close=regular (implicit)"),
        pytest.param(CLOSE_REGULAR, id="close=regular"),
        pytest.param(CLOSE_SPECIAL_REGULAR, id="close=special regular"),
        pytest.param(CLOSE_SPECIAL_AD_HOC, id="close=special ad-hoc"),
        pytest.param(CLOSE_SPECIAL_CUSTOM, id="close=special custom"),
    ],
)
@pytest.mark.parametrize(
    "open",
    [
        pytest.param(MISSING, id="open=inherit"),
        pytest.param("regular", id="open=regular (implicit)"),
        pytest.param(OPEN_REGULAR, id="open=regular"),
        pytest.param(OPEN_SPECIAL_REGULAR, id="open=special regular"),
        pytest.param(OPEN_SPECIAL_AD_HOC, id="open=special ad-hoc"),
        pytest.param(OPEN_SPECIAL_CUSTOM, id="open=special custom"),
    ],
)
@pytest.mark.parametrize(
    "set_name",
    [
        pytest.param("set", id="name=set"),
        pytest.param("inherit", id="name=inherit"),
        pytest.param("none", id="name=none"),
    ],
)
@pytest.mark.parametrize(
    "date,name_orig,type_orig",
    [
        _make_param_test_set_business_day(
            REGULAR_DAY_DT,
            None,
            "regular business day",
        ),
        _make_param_test_set_business_day(
            WEEKEND_DAY_DT,
            None,
            "regular weekend day",
            marks=_skip_below_threshold,
        ),
        _make_param_test_set_business_day(
            HOLIDAY_REGULAR_DT,
            HOLIDAY_REGULAR_NAME,
            "regular holiday",
        ),
        _make_param_test_set_business_day(
            HOLIDAY_ADHOC_DT,
            None,
            "ad-hoc holiday",
        ),
        _make_param_test_set_business_day(
            SPECIAL_OPEN_REGULAR_DT,
            SPECIAL_OPEN_REGULAR_NAME,
            "regular special open day",
        ),
        _make_param_test_set_business_day(
            SPECIAL_OPEN_ADHOC_DT,
            None,
            "ad-hoc special open day",
        ),
        _make_param_test_set_business_day(
            SPECIAL_CLOSE_REGULAR_DT,
            SPECIAL_CLOSE_REGULAR_NAME,
            "regular special close day",
        ),
        _make_param_test_set_business_day(
            SPECIAL_CLOSE_ADHOC_DT,
            None,
            "ad-hoc special close day",
        ),
    ],
)
def test_set_business_day(
    date: DateLike,
    name_orig: str | None,
    open: dt.time | Literal["regular"] | MISSING,
    close: dt.time | Literal["regular"] | MISSING,
    set_name: Literal["inherit", "none"],
    type_orig,
    test_calendar,
):
    name = MODIFIED_DAY_NAME

    c = test_calendar

    assigned_name, expected_name = get_assigned_and_expected_name(
        set_name, name, name_orig
    )

    original_open: tuple[Literal["regular", "adhoc", "normal"], dt.time, str | None] = (
        check_regular_special_session("special open", c, date)
    )
    original_close: tuple[
        Literal["regular", "adhoc", "normal"], dt.time, str | None
    ] = check_regular_special_session("special close", c, date)

    monthly_expiry_orig: bool | None = (
        not c.monthly_expiries.holidays(start=date, end=date, return_name=True).empty
        if c.monthly_expiries
        else None
    )
    quarterly_expiry_orig: bool | None = (
        not c.quarterly_expiries.holidays(start=date, end=date, return_name=True).empty
        if c.quarterly_expiries
        else None
    )

    ecx.change_day(
        exchange="TEST",
        date=date,
        action=DayChange(
            spec=BusinessDaySpec(open=open, close=close),
            name=assigned_name,
        ),
    )

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    # Day should not be in holidays.
    assert_not_in_holidays(c, date)

    open_time_expected = get_expected_session_time("open", open, original_open[1])
    close_time_expected = get_expected_session_time("close", close, original_close[1])

    if open_time_expected == OPEN_REGULAR and close_time_expected == CLOSE_REGULAR:
        # Regular session. Day should not be in special opens or closes.
        assert_not_in_special_sessions(date, c, "special open")
        assert_not_in_special_sessions(date, c, "special close")
    else:
        if open_time_expected != OPEN_REGULAR:
            # Day should be in special opens.
            assert_in_special_sessions(
                session_type="special open",
                calendar=c,
                date=date,
                name_orig=name_orig,
                assigned_name=assigned_name,
                expected_name=expected_name,
                expected_time=open_time_expected,
                orig=original_open,
            )
        else:
            assert_not_in_special_sessions(date, c, "special open")

        if close_time_expected != CLOSE_REGULAR:
            # Day should be in special closes.
            assert_in_special_sessions(
                session_type="special close",
                calendar=c,
                date=date,
                name_orig=name_orig,
                assigned_name=assigned_name,
                expected_name=expected_name,
                expected_time=close_time_expected,
                orig=original_close,
            )
        else:
            assert_not_in_special_sessions(date, c, "special close")

    # Check if day in monthly expiries, maybe.
    if monthly_expiry_orig is not None:
        assert c.monthly_expiries is not None and c.monthly_expiries.holidays(
            start=date, end=date, return_name=True
        ).empty == (monthly_expiry_orig is False)

    # Check if day in quarterly expiries, maybe.
    if quarterly_expiry_orig is not None:
        assert c.quarterly_expiries is not None and c.quarterly_expiries.holidays(
            start=date, end=date, return_name=True
        ).empty == (quarterly_expiry_orig is False)

    # Day should not be in weekend days.
    assert c.weekend_days.holidays(start=date, end=date, return_name=True).empty

    # Day should be in week days.
    s = c.week_days.holidays(start=date, end=date, return_name=True)
    assert_series_equal(s, {date: None})

    # Check if custom business day does not roll over day.
    assert date == c.day.rollforward(date)


@pytest.mark.isolated
def test_quarterly_expiry_rollback_one_day():
    add_extended_calendar_class(
        cls=create_test_calendar_class(
            holidays=[pd.Timestamp("2022-03-18")],
            adhoc_holidays=[],
            regular_special_close=dt.time(14, 00),
            special_closes=[],
            adhoc_special_closes=[],
            regular_special_open=dt.time(11, 00),
            special_opens=[],
            adhoc_special_opens=[],
            weekmask="1111100",
        ),
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    print(type(c))

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert c.quarterly_expiries is not None
    s = c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
    assert (
        isinstance(s, pd.Series)
        and (
            s.compare(
                pd.Series(
                    {
                        pd.Timestamp(
                            "2022-03-17"
                        ): None,  # Should be rolled back from 2022-03-18 since it is a holiday.
                        pd.Timestamp("2022-06-17"): None,
                        pd.Timestamp("2022-09-16"): None,
                        pd.Timestamp("2022-12-16"): None,
                    }
                )
            ).empty
        )
    )


@pytest.mark.isolated
def test_quarterly_expiry_rollback_multiple_days():
    add_extended_calendar_class(
        cls=create_test_calendar_class(
            holidays=[pd.Timestamp("2022-03-18")],
            adhoc_holidays=[pd.Timestamp("2022-03-17")],
            regular_special_close=dt.time(14, 00),
            special_closes=[(dt.time(14, 00), [pd.Timestamp("2022-03-16")])],
            adhoc_special_closes=[(dt.time(14, 00), [pd.Timestamp("2022-03-15")])],
            regular_special_open=dt.time(11, 00),
            special_opens=[(dt.time(11, 00), [pd.Timestamp("2022-03-14")])],
            adhoc_special_opens=[],
            weekmask="1111100",
        ),
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert c.quarterly_expiries is not None
    s = c.quarterly_expiries.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    pd.Timestamp(
                        "2022-03-11"
                    ): None,  # Should be rolled back from 2022-03-18.
                    pd.Timestamp("2022-06-17"): None,
                    pd.Timestamp("2022-09-16"): None,
                    pd.Timestamp("2022-12-16"): None,
                }
            )
        ).empty
    )


@pytest.mark.isolated
def test_monthly_expiry_rollback_one_day():
    add_extended_calendar_class(
        cls=create_test_calendar_class(
            holidays=[pd.Timestamp("2022-02-18")],
            adhoc_holidays=[],
            regular_special_close=dt.time(14, 00),
            special_closes=[],
            adhoc_special_closes=[],
            regular_special_open=dt.time(11, 00),
            special_opens=[],
            adhoc_special_opens=[],
            weekmask="1111100",
        ),
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert c.monthly_expiries is not None
    s = c.monthly_expiries.holidays(start=start, end=end, return_name=True)
    assert (
        isinstance(s, pd.Series)
        and (
            s.compare(
                pd.Series(
                    {
                        pd.Timestamp("2022-01-21"): None,
                        pd.Timestamp(
                            "2022-02-17"
                        ): None,  # Should be rolled back from 2022-02-18 since it is a holiday.
                        pd.Timestamp("2022-04-15"): None,
                        pd.Timestamp("2022-05-20"): None,
                        pd.Timestamp("2022-07-15"): None,
                        pd.Timestamp("2022-08-19"): None,
                        pd.Timestamp("2022-10-21"): None,
                        pd.Timestamp("2022-11-18"): None,
                    }
                )
            ).empty
        )
    )


@pytest.mark.isolated
def test_monthly_expiry_rollback_multiple_days():
    add_extended_calendar_class(
        cls=create_test_calendar_class(
            holidays=[pd.Timestamp("2022-02-18")],
            adhoc_holidays=[pd.Timestamp("2022-02-17")],
            regular_special_close=dt.time(14, 00),
            special_closes=[(dt.time(14, 00), [pd.Timestamp("2022-02-16")])],
            adhoc_special_closes=[(dt.time(14, 00), [pd.Timestamp("2022-02-15")])],
            regular_special_open=dt.time(11, 00),
            special_opens=[(dt.time(11, 00), [pd.Timestamp("2022-02-14")])],
            adhoc_special_opens=[],
            weekmask="1111100",
        ),
        day_of_week_expiry=4,
    )
    import exchange_calendars as ec

    c: ExtendedExchangeCalendar = cast(
        ExtendedExchangeCalendar, ec.get_calendar("TEST")
    )

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2022-12-31")

    assert c.monthly_expiries is not None
    s = c.monthly_expiries.holidays(start=start, end=end, return_name=True)
    assert isinstance(s, pd.Series) and (
        s.compare(
            pd.Series(
                {
                    pd.Timestamp("2022-01-21"): None,
                    pd.Timestamp(
                        "2022-02-11"
                    ): None,  # Should be rolled back from 2022-02-18.
                    pd.Timestamp("2022-04-15"): None,
                    pd.Timestamp("2022-05-20"): None,
                    pd.Timestamp("2022-07-15"): None,
                    pd.Timestamp("2022-08-19"): None,
                    pd.Timestamp("2022-10-21"): None,
                    pd.Timestamp("2022-11-18"): None,
                }
            )
        ).empty
    )


class TestTags:
    """Tests for the tags method of ExtendedExchangeCalendar."""

    @pytest.fixture
    def tagged_calendar(self, test_calendar) -> ExtendedExchangeCalendar:
        """Create a calendar with predefined tags for testing."""
        # Set up test tags on specific dates.
        ecx.change_day("TEST", "2023-01-10", DayChange(tags={"tag-a", "tag-b"}))
        ecx.change_day("TEST", "2023-01-15", DayChange(tags={"tag-a"}))
        ecx.change_day("TEST", "2023-01-20", DayChange(tags={"tag-b", "tag-c"}))
        ecx.change_day(
            "TEST", "2023-01-25", DayChange(tags={"tag-a", "tag-b", "tag-c"})
        )
        ecx.change_day("TEST", "2023-02-01", DayChange(tags={"tag-d"}))

        return cast(ExtendedExchangeCalendar, ec.get_calendar("TEST"))

    @pytest.mark.parametrize(
        "tags, start, end, expected_len, dates_in, dates_not_in",
        [
            # Non-existent tag in tagged calendar - returns empty
            ({"non-existent"}, None, None, 0, (), ()),
            # Empty tag set matches all tagged dates
            (set(), None, None, 5, (), ()),
            # Single tag: tag-a matches 3 dates
            (
                {"tag-a"},
                None,
                None,
                3,
                (
                    pd.Timestamp("2023-01-10"),
                    pd.Timestamp("2023-01-15"),
                    pd.Timestamp("2023-01-25"),
                ),
                (),
            ),
            # AND logic: tag-a AND tag-b matches 2 dates
            (
                {"tag-a", "tag-b"},
                None,
                None,
                2,
                (pd.Timestamp("2023-01-10"), pd.Timestamp("2023-01-25")),
                (),
            ),
            # AND logic: tag-b AND tag-c matches 2 dates
            (
                {"tag-b", "tag-c"},
                None,
                None,
                2,
                (pd.Timestamp("2023-01-20"), pd.Timestamp("2023-01-25")),
                (),
            ),
            # AND logic: all three tags match 1 date
            (
                {"tag-a", "tag-b", "tag-c"},
                None,
                None,
                1,
                (pd.Timestamp("2023-01-25"),),
                (),
            ),
            # Start date excludes first tag-a entry
            (
                {"tag-a"},
                pd.Timestamp("2023-01-11"),
                None,
                2,
                (pd.Timestamp("2023-01-15"), pd.Timestamp("2023-01-25")),
                (pd.Timestamp("2023-01-10"),),
            ),
            # End date excludes last tag-a entry
            (
                {"tag-a"},
                None,
                pd.Timestamp("2023-01-20"),
                2,
                (pd.Timestamp("2023-01-10"), pd.Timestamp("2023-01-15")),
                (pd.Timestamp("2023-01-25"),),
            ),
            # Start and end date narrow to middle tag-a entry only
            (
                {"tag-a"},
                pd.Timestamp("2023-01-11"),
                pd.Timestamp("2023-01-20"),
                1,
                (pd.Timestamp("2023-01-15"),),
                (),
            ),
            # Boundaries are inclusive: exact start/end match tagged dates
            (
                {"tag-a", "tag-b"},
                pd.Timestamp("2023-01-10"),
                pd.Timestamp("2023-01-25"),
                2,
                (pd.Timestamp("2023-01-10"), pd.Timestamp("2023-01-25")),
                (),
            ),
            # No overlap between date range and tagged dates
            (
                {"tag-a"},
                pd.Timestamp("2023-02-10"),
                pd.Timestamp("2023-02-20"),
                0,
                (),
                (),
            ),
            # Partial overlap: range 12th-18th includes 15th only
            (
                {"tag-a"},
                pd.Timestamp("2023-01-12"),
                pd.Timestamp("2023-01-18"),
                1,
                (pd.Timestamp("2023-01-15"),),
                (),
            ),
            # Partial overlap: range 12th-25th includes 15th and 25th
            (
                {"tag-a"},
                pd.Timestamp("2023-01-12"),
                pd.Timestamp("2023-01-25"),
                2,
                (pd.Timestamp("2023-01-15"), pd.Timestamp("2023-01-25")),
                (),
            ),
            # Explicit start=None, end=None returns all matching dates
            ({"tag-a"}, None, None, 3, (), ()),
            # Narrow range with Timestamp boundaries (date-as-string equivalent)
            (
                {"tag-a"},
                pd.Timestamp("2023-01-11"),
                pd.Timestamp("2023-01-31"),
                2,
                (),
                (),
            ),
        ],
    )
    def test_tags(
        self,
        tagged_calendar: ExtendedExchangeCalendar,
        tags: set,
        start: pd.Timestamp | None,
        end: pd.Timestamp | None,
        expected_len: int,
        dates_in: tuple,
        dates_not_in: tuple,
    ) -> None:
        """Test tags() with return_tags=False (default) across all parameter combinations."""
        c = tagged_calendar
        result = c.tags(tags=tags, start=start, end=end)
        assert isinstance(result, pd.DatetimeIndex)
        assert len(result) == expected_len
        for date in dates_in:
            assert date in result
        for date in dates_not_in:
            assert date not in result

    @pytest.mark.parametrize(
        "tags, start, end, expected_len, expected_tag_values",
        [
            # tag-a matches 3 dates; full tag sets are returned per date
            (
                {"tag-a"},
                None,
                None,
                3,
                {
                    pd.Timestamp("2023-01-10"): {"tag-a", "tag-b"},
                    pd.Timestamp("2023-01-15"): {"tag-a"},
                    pd.Timestamp("2023-01-25"): {"tag-a", "tag-b", "tag-c"},
                },
            ),
        ],
    )
    def test_tags_return_tags(
        self,
        tagged_calendar: ExtendedExchangeCalendar,
        tags: set,
        start: pd.Timestamp | None,
        end: pd.Timestamp | None,
        expected_len: int,
        expected_tag_values: dict,
    ) -> None:
        """Test tags() with return_tags=True returns a Series with tag sets per date."""
        c = tagged_calendar
        result = c.tags(tags=tags, start=start, end=end, return_tags=True)
        assert isinstance(result, pd.Series)
        assert len(result) == expected_len
        for date, expected_tags in expected_tag_values.items():
            assert result[date] == expected_tags
