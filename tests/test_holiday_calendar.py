from datetime import time

import pandas as pd
import pytest
from exchange_calendars import ExchangeCalendar, get_calendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.exchange_calendar import (
    HolidayCalendar as ExchangeCalendarsHolidayCalendar,
)
from exchange_calendars.exchange_calendar_xlon import ChristmasEve, NewYearsEvePost2000
from exchange_calendars.pandas_extensions.holiday import Holiday
from pytz import timezone

import tests.util
from exchange_calendars_extensions.core.holiday_calendar import (
    AdjustedHolidayCalendar,
    RollFn,
    get_days_calendar,
    get_holiday_calendar_from_day_of_week,
    get_holiday_calendar_from_timestamps,
    get_holidays_calendar,
    get_last_day_of_month_rules,
    get_monthly_expiry_rules,
    get_quadruple_witching_rules,
    get_special_closes_calendar,
    get_special_opens_calendar,
    merge_calendars,
    roll_one_day_same_month,
)
from exchange_calendars_extensions.core.util import WeekmaskPeriod
from tests.util import date2args, roll_backward, roll_forward

SPECIAL_OPEN = "special open"
SPECIAL_CLOSE = "special close"
QUARTERLY_EXPIRY = "quarterly expiry"
MONTHLY_EXPIRY = "monthly expiry"
LAST_DAY_OF_MONTH = "last day of month"
WEEKEND_DAY = "weekend day"
HOLIDAY = "Holiday"
OTHER_HOLIDAY = "Other Holiday"


class TestRollOneDaySameMonth:
    @pytest.mark.parametrize(
        "date",
        [
            pd.Timestamp("2020-01-02"),
            pd.Timestamp("2020-01-03"),
            pd.Timestamp("2020-01-04"),
        ],
    )
    def test_same_month(self, date: pd.Timestamp):
        print(date)
        print(roll_one_day_same_month(date))
        print(date - pd.Timedelta(days=1))
        assert roll_one_day_same_month(date) == date - pd.Timedelta(days=1)

    @pytest.mark.parametrize(
        "date",
        [
            pd.Timestamp("2020-01-01"),
            pd.Timestamp("2020-02-01"),
            pd.Timestamp("2020-03-01"),
        ],
    )
    def test_not_same_month(self, date: pd.Timestamp):
        assert roll_one_day_same_month(date) is None


class TestAdjustedHolidayCalendar:
    @pytest.mark.parametrize(
        "return_name", [False, True], ids=["return_name=False", "return_name=True"]
    )
    @pytest.mark.parametrize(
        "weekmask, day, day_adjusted, roll_fn",
        [
            ("1111100", "2024-01-15", "2024-01-15", roll_backward),  # Mon
            ("1111100", "2024-01-16", "2024-01-16", roll_backward),  # Tue
            ("1111100", "2024-01-17", "2024-01-17", roll_backward),  # Wed
            ("1111100", "2024-01-18", "2024-01-18", roll_backward),  # Thu
            ("1111100", "2024-01-19", "2024-01-19", roll_backward),  # Fri
            ("1111100", "2024-01-20", "2024-01-19", roll_backward),  # Sat
            ("1111100", "2024-01-21", "2024-01-19", roll_backward),  # Sun
            ("1111100", "2024-01-15", "2024-01-15", roll_forward),  # Mon
            ("1111100", "2024-01-16", "2024-01-16", roll_forward),  # Tue
            ("1111100", "2024-01-17", "2024-01-17", roll_forward),  # Wed
            ("1111100", "2024-01-18", "2024-01-18", roll_forward),  # Thu
            ("1111100", "2024-01-19", "2024-01-19", roll_forward),  # Fri
            ("1111100", "2024-01-20", "2024-01-22", roll_forward),  # Sat
            ("1111100", "2024-01-21", "2024-01-22", roll_forward),  # Sun
        ],
    )
    def test_weekmask(
        self,
        weekmask: str,
        day: str,
        day_adjusted: str,
        roll_fn: RollFn,
        return_name: bool,
    ):
        """Test that the weekmask is applied correctly when adjusting the holidays."""

        # Unadjusted holiday.
        day = pd.Timestamp(day)

        # Adjusted holiday.
        day_adjusted = pd.Timestamp(day_adjusted)

        # Calendar containing just the single holiday, the given weekmask, and using the given roll function. The other
        # calendar is empty.
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(day)),
            ],
            other=ExchangeCalendarsHolidayCalendar([]),
            weekmask_periods=(WeekmaskPeriod(weekmask=weekmask),),
            roll_fn=roll_fn,
        )

        # Check that holiday is adjusted to the expected day.
        assert calendar.holidays(return_name=return_name).equals(
            pd.Series(
                [
                    HOLIDAY,
                ],
                index=[
                    day_adjusted,
                ],
            )
            if return_name
            else pd.DatetimeIndex(
                [
                    day_adjusted,
                ]
            )
        )

    @pytest.mark.parametrize(
        "return_name", [False, True], ids=["return_name=False", "return_name=True"]
    )
    @pytest.mark.parametrize(
        "day, day_adjusted, day_other, roll_fn",
        [
            (
                "2024-01-15",
                "2024-01-15",
                "2024-01-16",
                roll_backward,
            ),  # Day after holiday is a holiday. No adjustment.
            (
                "2024-01-16",
                "2024-01-15",
                "2024-01-16",
                roll_backward,
            ),  # Day coincides with other holiday. Adjust.
            (
                "2024-01-17",
                "2024-01-17",
                "2024-01-16",
                roll_backward,
            ),  # Day before holiday is a holiday. No adjustment.
            (
                "2024-01-15",
                "2024-01-15",
                "2024-01-16",
                roll_forward,
            ),  # Day after holiday is a holiday. No adjustment.
            (
                "2024-01-16",
                "2024-01-17",
                "2024-01-16",
                roll_forward,
            ),  # Day coincides with other holiday. Adjust.
            (
                "2024-01-17",
                "2024-01-17",
                "2024-01-16",
                roll_forward,
            ),  # Day before holiday is a holiday. No adjustment.
        ],
    )
    def test_other_calendar(
        self,
        day: str,
        day_adjusted: str,
        day_other: str,
        roll_fn: RollFn,
        return_name: bool,
    ):
        """Test that the other given calendar is applied correctly when adjusting the holidays."""

        # Unadjusted holiday.
        day = pd.Timestamp(day)

        # Adjusted holiday.
        day_adjusted = pd.Timestamp(day_adjusted)

        # Holiday in other calendar.
        day_other = pd.Timestamp(day_other)

        # Calendar containing the single holiday, and another holiday in the other given calendar. The weekmask covers
        # all days of the week, so it should not have any impact on adjustments. Also uses the given roll function.
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(day)),
            ],
            other=ExchangeCalendarsHolidayCalendar(
                rules=[
                    Holiday(name=HOLIDAY, **date2args(day_other)),
                ]
            ),
            weekmask_periods=(WeekmaskPeriod(weekmask="1111111"),),
            roll_fn=roll_fn,
        )

        # Test that the holidays are adjusted correctly.
        assert calendar.holidays(return_name=return_name).equals(
            pd.Series(
                [
                    HOLIDAY,
                ],
                index=[
                    day_adjusted,
                ],
            )
            if return_name
            else pd.DatetimeIndex(
                [
                    day_adjusted,
                ]
            )
        )

    def test_multiple_adjustments_and_roll_fn(self, mocker):
        """Test that the roll function is called multiple times when necessary."""

        # A Monday.
        mon = pd.Timestamp("2024-01-15")

        # The previous Friday.
        fri = mon - pd.Timedelta(days=3)

        # The Thursday before the previous Friday.
        thu = fri - pd.Timedelta(days=1)

        # Create a spy on the roll_backward function.
        spy_roll_fn = mocker.spy(tests.util, "roll_backward")

        # Calendar with mon as a0 holiday. In the given other calendar, mon is a holiday as well, as is fri. The
        # weekmask covers all days of the week, so it should not have any impact on adjustments. Also uses the given
        # roll function.
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(mon)),  # Monday.
            ],
            other=ExchangeCalendarsHolidayCalendar(
                rules=[
                    Holiday(
                        name="Other Holiday 1", **date2args(fri)
                    ),  # Previous Friday.
                    Holiday(name="Other Holiday 2", **date2args(mon)),  # Monday.
                ]
            ),
            weekmask_periods=(WeekmaskPeriod(weekmask="1111100"),),
            roll_fn=spy_roll_fn,
        )

        # Check if the holiday is adjusted correctly. It should be rolled back to the previous Thrusday.
        assert calendar.holidays().equals(
            pd.DatetimeIndex(
                [
                    thu,
                ]
            )
        )

        # Should have rolled four times.
        assert spy_roll_fn.call_count == 4

        # Check expected arguments to roll function.
        assert spy_roll_fn.call_args_list == [
            mocker.call(mon),
            mocker.call(mon - pd.Timedelta(days=1)),
            mocker.call(mon - pd.Timedelta(days=2)),
            mocker.call(mon - pd.Timedelta(days=3)),
        ]

    def test_roll_fn_returns_none(self, mocker):
        """Test case where the roll function returns None."""

        # Mock the roll function to always return None.
        mock_roll_fn = mocker.Mock()
        mock_roll_fn.side_effect = lambda day: None

        # Single holiday to test.
        day = pd.Timestamp("2024-01-15")

        # Calendar with a holiday that conflicts with a holiday in the other calendar. The weekmask is set to Monday to
        # Sunday.
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(day)),
            ],
            other=ExchangeCalendarsHolidayCalendar(
                rules=[
                    Holiday(name=HOLIDAY, **date2args(day)),
                ]
            ),
            weekmask_periods=WeekmaskPeriod(weekmask="1111111"),
            roll_fn=mock_roll_fn,
        )

        # Check if holiday gets dropped due to the roll function returning None.
        assert calendar.holidays().equals(pd.DatetimeIndex([]))

        # Should have rolled a single time.
        mock_roll_fn.assert_called_once_with(day)

    @pytest.mark.parametrize("roll_fn", [roll_backward, roll_forward])
    def test_internal_conflict(self, roll_fn: RollFn):
        """Test case where a holiday conflicts with another one defined in the same calendar."""

        # Arbitrary day to use as holiday.
        day = pd.Timestamp("2024-01-15")

        # Adjusted holiday.
        day_adjusted = roll_fn(day)

        # Calendar with conflicting rules. The given other calendar is empty. The weekmask covers all days of the week,
        # so it should not have any impact on adjustments. Also uses the given roll function.
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(day)),  # Mon
                Holiday(name=HOLIDAY, **date2args(day)),  # Same day as holiday above.
            ],
            other=ExchangeCalendarsHolidayCalendar([]),
            weekmask_periods=(WeekmaskPeriod(weekmask="1111111"),),
            roll_fn=roll_fn,
        )

        # Check if the holidays are adjusted in order of definition, i.e. Holiday gets adjusted by roll_fn, Other
        # Holiday remains untouched.
        assert calendar.holidays(return_name=True).equals(
            pd.Series(
                [
                    HOLIDAY,
                    HOLIDAY,
                ],
                index=[
                    day_adjusted,
                    day,
                ],
            )
        )

    def test_roll_precedence(self):
        """Test case where a holiday gets rolled back due to a conflict with a holiday in another calendar, but then,
        after the first adjustment, conflicts with a holiday defined in the same calendar."""

        # Arbitrary day to use as holiday.
        day = pd.Timestamp("2024-01-15")

        # The day after.
        day_after = day + pd.Timedelta(days=1)

        # The day before.
        day_before = day - pd.Timedelta(days=1)

        # Calendar with conflicting rules. The rule for Holiday 2 conflicts with the rule for Other Holiday in the given
        # other calendar. The weekmask covers all days of the week, so it should not have any impact on adjustments.
        # Uses a roll function that rolls back one day.
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name="Holiday 1", **date2args(day)),
                Holiday(name="Holiday 2", **date2args(day_after)),
            ],
            other=ExchangeCalendarsHolidayCalendar(
                rules=[
                    Holiday(name=HOLIDAY, **date2args(day_after)),
                ]
            ),
            weekmask_periods=(WeekmaskPeriod(weekmask="1111111"),),
            roll_fn=roll_backward,
        )

        # Holiday 2 should first be adjusted to `day` due to the conflict with Other Holiday. Then, Holiday 1
        # should be adjusted to `day_before` due to the conflict with the adjusted Holiday 2.
        assert calendar.holidays(return_name=True).equals(
            pd.Series(
                [
                    "Holiday 1",
                    "Holiday 2",
                ],
                index=[
                    day_before,
                    day,
                ],
            )
        )

    @pytest.mark.parametrize("roll_fn", [roll_backward, roll_forward])
    def test_roll_outside_range(self, roll_fn: RollFn):
        """Test case where a holiday gets rolled back due to a conflict with a holiday in another calendar, but then
        falls outside the requested date range."""

        # Arbitrary day to use as holiday.
        day = pd.Timestamp("2024-01-15")

        # Adjusted holiday.
        day_adjusted = roll_fn(day)

        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(day)),
            ],
            other=ExchangeCalendarsHolidayCalendar(
                rules=[
                    Holiday(name=HOLIDAY, **date2args(day)),
                ]
            ),
            weekmask_periods=(WeekmaskPeriod(weekmask="1111111"),),
            roll_fn=roll_fn,
        )

        # Adjusted holiday should be different from unadjusted one.
        assert day_adjusted != day

        # Holiday should be adjusted by rolling once due to the conflict with Other Holiday.
        assert calendar.holidays(return_name=True).equals(
            pd.Series(
                [
                    HOLIDAY,
                ],
                index=[
                    day_adjusted,
                ],
            )
        )

        # Holiday should not be included when the requested date range only covers the original date, although the
        # unadjusted date falls within.
        assert calendar.holidays(start=day, end=day, return_name=True).equals(
            pd.Series([], dtype="object")
        )


class TestHolidayCalendars:
    def test_get_holiday_calendar_from_timestamps(self):
        timestamps = [pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")]
        calendar = get_holiday_calendar_from_timestamps(timestamps)
        holidays = calendar.holidays(
            start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31")
        )
        assert pd.Timestamp("2019-01-01") in holidays
        assert pd.Timestamp("2019-01-02") in holidays
        assert pd.Timestamp("2019-01-03") not in holidays
        assert pd.Timestamp("2019-01-04") not in holidays

    def test_get_holiday_calendar_from_day_of_week(self):
        calendar = get_holiday_calendar_from_day_of_week(0)
        holidays = calendar.holidays(
            start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31")
        )
        assert pd.Timestamp("2019-01-07") in holidays
        assert pd.Timestamp("2019-01-14") in holidays
        assert pd.Timestamp("2019-01-21") in holidays
        assert pd.Timestamp("2019-01-28") in holidays
        assert pd.Timestamp("2019-01-01") not in holidays
        assert pd.Timestamp("2019-01-02") not in holidays
        assert pd.Timestamp("2019-01-03") not in holidays
        assert pd.Timestamp("2019-01-04") not in holidays
        assert pd.Timestamp("2019-01-05") not in holidays
        assert pd.Timestamp("2019-01-06") not in holidays
        assert pd.Timestamp("2019-01-08") not in holidays
        assert pd.Timestamp("2019-01-09") not in holidays
        assert pd.Timestamp("2019-01-10") not in holidays
        assert pd.Timestamp("2019-01-11") not in holidays
        assert pd.Timestamp("2019-01-12") not in holidays
        assert pd.Timestamp("2019-01-13") not in holidays
        assert pd.Timestamp("2019-01-15") not in holidays
        assert pd.Timestamp("2019-01-16") not in holidays
        assert pd.Timestamp("2019-01-17") not in holidays
        assert pd.Timestamp("2019-01-18") not in holidays
        assert pd.Timestamp("2019-01-19") not in holidays
        assert pd.Timestamp("2019-01-20") not in holidays

    def test_merge_calendars(self):
        calendar1 = get_holiday_calendar_from_timestamps(
            [pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")]
        )
        calendar2 = get_holiday_calendar_from_day_of_week(0)
        calendar = merge_calendars((calendar1, calendar2))
        holidays = calendar.holidays(
            start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31")
        )
        assert pd.Timestamp("2019-01-01") in holidays
        assert pd.Timestamp("2019-01-02") in holidays
        assert pd.Timestamp("2019-01-07") in holidays
        assert pd.Timestamp("2019-01-14") in holidays
        assert pd.Timestamp("2019-01-21") in holidays
        assert pd.Timestamp("2019-01-28") in holidays
        assert pd.Timestamp("2019-01-03") not in holidays
        assert pd.Timestamp("2019-01-04") not in holidays
        assert pd.Timestamp("2019-01-05") not in holidays
        assert pd.Timestamp("2019-01-06") not in holidays
        assert pd.Timestamp("2019-01-08") not in holidays
        assert pd.Timestamp("2019-01-09") not in holidays
        assert pd.Timestamp("2019-01-10") not in holidays
        assert pd.Timestamp("2019-01-11") not in holidays
        assert pd.Timestamp("2019-01-12") not in holidays
        assert pd.Timestamp("2019-01-13") not in holidays
        assert pd.Timestamp("2019-01-15") not in holidays
        assert pd.Timestamp("2019-01-16") not in holidays
        assert pd.Timestamp("2019-01-17") not in holidays
        assert pd.Timestamp("2019-01-18") not in holidays
        assert pd.Timestamp("2019-01-19") not in holidays
        assert pd.Timestamp("2019-01-20") not in holidays
        assert pd.Timestamp("2019-01-22") not in holidays
        assert pd.Timestamp("2019-01-23") not in holidays
        assert pd.Timestamp("2019-01-24") not in holidays
        assert pd.Timestamp("2019-01-25") not in holidays

    def test_merge_calendars_with_overlapping_holidays(self):
        calendar1 = get_holiday_calendar_from_timestamps(
            [pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")]
        )
        calendar2 = get_holiday_calendar_from_timestamps(
            [pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-03")]
        )
        calendar = merge_calendars((calendar1, calendar2))
        holidays = calendar.holidays(
            start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31")
        )
        assert len(holidays) == 3
        assert pd.Timestamp("2019-01-01") in holidays
        assert pd.Timestamp("2019-01-02") in holidays
        assert pd.Timestamp("2019-01-03") in holidays
        assert pd.Timestamp("2019-01-04") not in holidays

    def test_get_holidays_calendar(self):
        calendar = get_calendar("XLON")
        holidays_calendar = get_holidays_calendar(calendar)
        holidays = holidays_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_holidays = pd.Series(
            {
                pd.Timestamp("2020-01-01"): "New Year's Day",
                pd.Timestamp("2020-04-10"): "Good Friday",
                pd.Timestamp("2020-04-13"): "Easter Monday",
                pd.Timestamp("2020-05-08"): "ad-hoc holiday",
                pd.Timestamp("2020-05-25"): "Spring Bank Holiday",
                pd.Timestamp("2020-08-31"): "Summer Bank Holiday",
                pd.Timestamp("2020-12-25"): "Christmas",
                pd.Timestamp("2020-12-26"): "Boxing Day",
                pd.Timestamp("2020-12-28"): "Weekend Boxing Day",
            }
        )
        assert holidays.compare(expected_holidays).empty

    def test_get_special_closes_calendar(self):
        class TestCalendar(ExchangeCalendar):
            regular_early_close = time(12, 30)
            name = "TEST"
            tz = timezone("Europe/London")
            open_times = ((None, time(8)),)
            close_times = ((None, time(16, 30)),)

            @property
            def regular_holidays(self):
                return HolidayCalendar([])

            @property
            def adhoc_holidays(self):
                return []

            @property
            def special_closes(self):
                return [
                    (
                        self.regular_early_close,
                        HolidayCalendar(
                            [
                                ChristmasEve,
                                NewYearsEvePost2000,
                            ]
                        ),
                    ),
                    (time(11, 30), 0),  # Monday
                ]

            @property
            def special_closes_adhoc(self):
                return [
                    (
                        self.regular_early_close,
                        pd.DatetimeIndex(
                            [
                                pd.Timestamp("2020-01-08"),
                                pd.Timestamp("2020-08-12"),
                            ]
                        ),
                    )
                ]

            ...

        calendar = TestCalendar()
        special_closes_calendar = get_special_closes_calendar(calendar)
        special_closes = special_closes_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_special_closes = pd.Series(
            {
                pd.Timestamp("2020-01-06"): SPECIAL_CLOSE,
                pd.Timestamp("2020-01-08"): "ad-hoc special close",
                pd.Timestamp("2020-01-13"): SPECIAL_CLOSE,
                pd.Timestamp("2020-01-20"): SPECIAL_CLOSE,
                pd.Timestamp("2020-01-27"): SPECIAL_CLOSE,
                pd.Timestamp("2020-02-03"): SPECIAL_CLOSE,
                pd.Timestamp("2020-02-10"): SPECIAL_CLOSE,
                pd.Timestamp("2020-02-17"): SPECIAL_CLOSE,
                pd.Timestamp("2020-02-24"): SPECIAL_CLOSE,
                pd.Timestamp("2020-03-02"): SPECIAL_CLOSE,
                pd.Timestamp("2020-03-09"): SPECIAL_CLOSE,
                pd.Timestamp("2020-03-16"): SPECIAL_CLOSE,
                pd.Timestamp("2020-03-23"): SPECIAL_CLOSE,
                pd.Timestamp("2020-03-30"): SPECIAL_CLOSE,
                pd.Timestamp("2020-04-06"): SPECIAL_CLOSE,
                pd.Timestamp("2020-04-13"): SPECIAL_CLOSE,
                pd.Timestamp("2020-04-20"): SPECIAL_CLOSE,
                pd.Timestamp("2020-04-27"): SPECIAL_CLOSE,
                pd.Timestamp("2020-05-04"): SPECIAL_CLOSE,
                pd.Timestamp("2020-05-11"): SPECIAL_CLOSE,
                pd.Timestamp("2020-05-18"): SPECIAL_CLOSE,
                pd.Timestamp("2020-05-25"): SPECIAL_CLOSE,
                pd.Timestamp("2020-06-01"): SPECIAL_CLOSE,
                pd.Timestamp("2020-06-08"): SPECIAL_CLOSE,
                pd.Timestamp("2020-06-15"): SPECIAL_CLOSE,
                pd.Timestamp("2020-06-22"): SPECIAL_CLOSE,
                pd.Timestamp("2020-06-29"): SPECIAL_CLOSE,
                pd.Timestamp("2020-07-06"): SPECIAL_CLOSE,
                pd.Timestamp("2020-07-13"): SPECIAL_CLOSE,
                pd.Timestamp("2020-07-20"): SPECIAL_CLOSE,
                pd.Timestamp("2020-07-27"): SPECIAL_CLOSE,
                pd.Timestamp("2020-08-03"): SPECIAL_CLOSE,
                pd.Timestamp("2020-08-10"): SPECIAL_CLOSE,
                pd.Timestamp("2020-08-12"): "ad-hoc special close",
                pd.Timestamp("2020-08-17"): SPECIAL_CLOSE,
                pd.Timestamp("2020-08-24"): SPECIAL_CLOSE,
                pd.Timestamp("2020-08-31"): SPECIAL_CLOSE,
                pd.Timestamp("2020-09-07"): SPECIAL_CLOSE,
                pd.Timestamp("2020-09-14"): SPECIAL_CLOSE,
                pd.Timestamp("2020-09-21"): SPECIAL_CLOSE,
                pd.Timestamp("2020-09-28"): SPECIAL_CLOSE,
                pd.Timestamp("2020-10-05"): SPECIAL_CLOSE,
                pd.Timestamp("2020-10-12"): SPECIAL_CLOSE,
                pd.Timestamp("2020-10-19"): SPECIAL_CLOSE,
                pd.Timestamp("2020-10-26"): SPECIAL_CLOSE,
                pd.Timestamp("2020-11-02"): SPECIAL_CLOSE,
                pd.Timestamp("2020-11-09"): SPECIAL_CLOSE,
                pd.Timestamp("2020-11-16"): SPECIAL_CLOSE,
                pd.Timestamp("2020-11-23"): SPECIAL_CLOSE,
                pd.Timestamp("2020-11-30"): SPECIAL_CLOSE,
                pd.Timestamp("2020-12-07"): SPECIAL_CLOSE,
                pd.Timestamp("2020-12-14"): SPECIAL_CLOSE,
                pd.Timestamp("2020-12-21"): SPECIAL_CLOSE,
                pd.Timestamp("2020-12-24"): "Christmas Eve",
                pd.Timestamp("2020-12-28"): SPECIAL_CLOSE,
                pd.Timestamp("2020-12-31"): "New Year's Eve",
            }
        )
        assert special_closes.compare(expected_special_closes).empty

    def test_get_special_opens_calendar(self):
        class TestCalendar(ExchangeCalendar):
            regular_late_open = time(10, 30)
            name = "TEST"
            tz = timezone("Europe/London")
            open_times = ((None, time(8)),)
            close_times = ((None, time(16, 30)),)

            @property
            def regular_holidays(self):
                return HolidayCalendar([])

            @property
            def adhoc_holidays(self):
                return []

            @property
            def special_opens(self):
                return [
                    (
                        self.regular_late_open,
                        HolidayCalendar(
                            [
                                ChristmasEve,
                                NewYearsEvePost2000,
                            ]
                        ),
                    ),
                    (time(11, 30), 0),  # Monday
                ]

            @property
            def special_opens_adhoc(self):
                return [
                    (
                        self.regular_late_open,
                        pd.DatetimeIndex(
                            [
                                pd.Timestamp("2020-01-08"),
                                pd.Timestamp("2020-08-12"),
                            ]
                        ),
                    )
                ]

            ...

        calendar = TestCalendar()
        special_opens_calendar = get_special_opens_calendar(calendar)
        special_opens = special_opens_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_special_opens = pd.Series(
            {
                pd.Timestamp("2020-01-06"): SPECIAL_OPEN,
                pd.Timestamp("2020-01-08"): "ad-hoc special open",
                pd.Timestamp("2020-01-13"): SPECIAL_OPEN,
                pd.Timestamp("2020-01-20"): SPECIAL_OPEN,
                pd.Timestamp("2020-01-27"): SPECIAL_OPEN,
                pd.Timestamp("2020-02-03"): SPECIAL_OPEN,
                pd.Timestamp("2020-02-10"): SPECIAL_OPEN,
                pd.Timestamp("2020-02-17"): SPECIAL_OPEN,
                pd.Timestamp("2020-02-24"): SPECIAL_OPEN,
                pd.Timestamp("2020-03-02"): SPECIAL_OPEN,
                pd.Timestamp("2020-03-09"): SPECIAL_OPEN,
                pd.Timestamp("2020-03-16"): SPECIAL_OPEN,
                pd.Timestamp("2020-03-23"): SPECIAL_OPEN,
                pd.Timestamp("2020-03-30"): SPECIAL_OPEN,
                pd.Timestamp("2020-04-06"): SPECIAL_OPEN,
                pd.Timestamp("2020-04-13"): SPECIAL_OPEN,
                pd.Timestamp("2020-04-20"): SPECIAL_OPEN,
                pd.Timestamp("2020-04-27"): SPECIAL_OPEN,
                pd.Timestamp("2020-05-04"): SPECIAL_OPEN,
                pd.Timestamp("2020-05-11"): SPECIAL_OPEN,
                pd.Timestamp("2020-05-18"): SPECIAL_OPEN,
                pd.Timestamp("2020-05-25"): SPECIAL_OPEN,
                pd.Timestamp("2020-06-01"): SPECIAL_OPEN,
                pd.Timestamp("2020-06-08"): SPECIAL_OPEN,
                pd.Timestamp("2020-06-15"): SPECIAL_OPEN,
                pd.Timestamp("2020-06-22"): SPECIAL_OPEN,
                pd.Timestamp("2020-06-29"): SPECIAL_OPEN,
                pd.Timestamp("2020-07-06"): SPECIAL_OPEN,
                pd.Timestamp("2020-07-13"): SPECIAL_OPEN,
                pd.Timestamp("2020-07-20"): SPECIAL_OPEN,
                pd.Timestamp("2020-07-27"): SPECIAL_OPEN,
                pd.Timestamp("2020-08-03"): SPECIAL_OPEN,
                pd.Timestamp("2020-08-10"): SPECIAL_OPEN,
                pd.Timestamp("2020-08-12"): "ad-hoc special open",
                pd.Timestamp("2020-08-17"): SPECIAL_OPEN,
                pd.Timestamp("2020-08-24"): SPECIAL_OPEN,
                pd.Timestamp("2020-08-31"): SPECIAL_OPEN,
                pd.Timestamp("2020-09-07"): SPECIAL_OPEN,
                pd.Timestamp("2020-09-14"): SPECIAL_OPEN,
                pd.Timestamp("2020-09-21"): SPECIAL_OPEN,
                pd.Timestamp("2020-09-28"): SPECIAL_OPEN,
                pd.Timestamp("2020-10-05"): SPECIAL_OPEN,
                pd.Timestamp("2020-10-12"): SPECIAL_OPEN,
                pd.Timestamp("2020-10-19"): SPECIAL_OPEN,
                pd.Timestamp("2020-10-26"): SPECIAL_OPEN,
                pd.Timestamp("2020-11-02"): SPECIAL_OPEN,
                pd.Timestamp("2020-11-09"): SPECIAL_OPEN,
                pd.Timestamp("2020-11-16"): SPECIAL_OPEN,
                pd.Timestamp("2020-11-23"): SPECIAL_OPEN,
                pd.Timestamp("2020-11-30"): SPECIAL_OPEN,
                pd.Timestamp("2020-12-07"): SPECIAL_OPEN,
                pd.Timestamp("2020-12-14"): SPECIAL_OPEN,
                pd.Timestamp("2020-12-21"): SPECIAL_OPEN,
                pd.Timestamp("2020-12-24"): "Christmas Eve",
                pd.Timestamp("2020-12-28"): SPECIAL_OPEN,
                pd.Timestamp("2020-12-31"): "New Year's Eve",
            }
        )
        assert special_opens.compare(expected_special_opens).empty

    def test_get_weekend_days_calendar(self):
        class TestCalendar(ExchangeCalendar):
            name = "TEST"
            tz = timezone("Europe/London")
            open_times = ((None, time(8)),)
            close_times = ((None, time(16, 30)),)
            weekmask = "1111010"

        calendar = TestCalendar()
        weekend_days_calendar = get_days_calendar(calendar, mask="0")
        weekend_days = weekend_days_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-01-31"),
            return_name=True,
        )
        expected_weekend_days = pd.Series(
            {
                pd.Timestamp("2020-01-03"): WEEKEND_DAY,
                pd.Timestamp("2020-01-05"): WEEKEND_DAY,
                pd.Timestamp("2020-01-10"): WEEKEND_DAY,
                pd.Timestamp("2020-01-12"): WEEKEND_DAY,
                pd.Timestamp("2020-01-17"): WEEKEND_DAY,
                pd.Timestamp("2020-01-19"): WEEKEND_DAY,
                pd.Timestamp("2020-01-24"): WEEKEND_DAY,
                pd.Timestamp("2020-01-26"): WEEKEND_DAY,
                pd.Timestamp("2020-01-31"): WEEKEND_DAY,
            }
        )

        assert weekend_days.compare(expected_weekend_days).empty

    def test_get_monthly_expiry_calendar(self):
        # Test plain vanilla calendar without any special days or close days that may fall onto the same days as monthly
        # expiry.

        monthly_expiry_calendar = HolidayCalendar(
            rules=get_monthly_expiry_rules(day_of_week=4)
        )
        monthly_expiry = monthly_expiry_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_monthly_expiry = pd.Series(
            {
                pd.Timestamp("2020-01-17"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-02-21"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-04-17"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-05-15"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-07-17"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-08-21"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-10-16"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-11-20"): MONTHLY_EXPIRY,
            }
        )

        assert monthly_expiry.compare(expected_monthly_expiry).empty

        # Test calendar with identity observance.
        monthly_expiry_calendar = HolidayCalendar(
            rules=get_monthly_expiry_rules(day_of_week=4, observance=lambda x: x)
        )
        monthly_expiry = monthly_expiry_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_monthly_expiry = pd.Series(
            {
                pd.Timestamp("2020-01-17"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-02-21"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-04-17"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-05-15"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-07-17"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-08-21"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-10-16"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-11-20"): MONTHLY_EXPIRY,
            }
        )

        assert monthly_expiry.compare(expected_monthly_expiry).empty

        # Test calendar with an observance that moves the holiday to the previous day.
        monthly_expiry_calendar = HolidayCalendar(
            rules=get_monthly_expiry_rules(
                day_of_week=4, observance=lambda x: x - pd.Timedelta(days=1)
            )
        )
        monthly_expiry = monthly_expiry_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_monthly_expiry = pd.Series(
            {
                pd.Timestamp("2020-01-16"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-02-20"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-04-16"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-05-14"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-07-16"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-08-20"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-10-15"): MONTHLY_EXPIRY,
                pd.Timestamp("2020-11-19"): MONTHLY_EXPIRY,
            }
        )

        assert monthly_expiry.compare(expected_monthly_expiry).empty

    def test_get_quadruple_witching_calendar(self):
        # Test plain vanilla calendar without any special days or close days that may fall onto the same days as quarterly
        # expiry.
        quarterly_expiry_calendar = HolidayCalendar(
            rules=get_quadruple_witching_rules(day_of_week=4)
        )
        quarterly_expiry = quarterly_expiry_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_quarterly_expiry = pd.Series(
            {
                pd.Timestamp("2020-03-20"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-06-19"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-09-18"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-12-18"): QUARTERLY_EXPIRY,
            }
        )

        assert quarterly_expiry.compare(expected_quarterly_expiry).empty

        # Test calendar with identity observance.
        quarterly_expiry_calendar = HolidayCalendar(
            rules=get_quadruple_witching_rules(day_of_week=4, observance=lambda x: x)
        )
        quarterly_expiry = quarterly_expiry_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_quarterly_expiry = pd.Series(
            {
                pd.Timestamp("2020-03-20"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-06-19"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-09-18"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-12-18"): QUARTERLY_EXPIRY,
            }
        )

        assert quarterly_expiry.compare(expected_quarterly_expiry).empty

        # Test calendar with an observance that moves the holiday to the previous day.
        quarterly_expiry_calendar = HolidayCalendar(
            rules=get_quadruple_witching_rules(
                day_of_week=4, observance=lambda x: x - pd.Timedelta(days=1)
            )
        )
        quarterly_expiry = quarterly_expiry_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_quarterly_expiry = pd.Series(
            {
                pd.Timestamp("2020-03-19"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-06-18"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-09-17"): QUARTERLY_EXPIRY,
                pd.Timestamp("2020-12-17"): QUARTERLY_EXPIRY,
            }
        )

        assert quarterly_expiry.compare(expected_quarterly_expiry).empty

    def test_get_last_day_of_month_calendar(self):
        # Test plain vanilla calendar that ignores any special days or close days, even weekends, that may fall onto the
        # same days.
        last_day_of_month_calendar = HolidayCalendar(
            rules=get_last_day_of_month_rules(name=LAST_DAY_OF_MONTH)
        )
        last_day_of_month = last_day_of_month_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_last_day_of_month = pd.Series(
            {
                pd.Timestamp("2020-01-31"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-02-29"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-03-31"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-04-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-05-31"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-06-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-07-31"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-08-31"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-09-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-10-31"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-11-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-12-31"): LAST_DAY_OF_MONTH,
            }
        )

        assert last_day_of_month.compare(expected_last_day_of_month).empty

        # Test calendar with an observance that moves the holiday to the previous day.
        last_day_of_month_calendar = HolidayCalendar(
            rules=get_last_day_of_month_rules(
                name=LAST_DAY_OF_MONTH, observance=lambda x: x - pd.Timedelta(days=1)
            )
        )
        last_day_of_month = last_day_of_month_calendar.holidays(
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-12-31"),
            return_name=True,
        )
        expected_last_day_of_month = pd.Series(
            {
                pd.Timestamp("2020-01-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-02-28"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-03-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-04-29"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-05-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-06-29"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-07-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-08-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-09-29"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-10-30"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-11-29"): LAST_DAY_OF_MONTH,
                pd.Timestamp("2020-12-30"): LAST_DAY_OF_MONTH,
            }
        )

        assert last_day_of_month.compare(expected_last_day_of_month).empty


class TestAdjustedHolidayCalendarWithMultipleWeekmaskPeriods:
    """Test AdjustedHolidayCalendar with multiple weekmask periods."""

    def test_roll_within_single_period(self):
        """Test that rolling works correctly within a single period."""
        # A single period: Jan 1-31, Mon-Fri open (Sat/Sun weekend)
        periods = (
            WeekmaskPeriod(
                weekmask="1111100",  # Mon-Fri open
                start_date=pd.Timestamp("2024-01-01"),
                end_date=pd.Timestamp("2024-01-31"),
            ),
        )

        # Holiday on Saturday Jan 6, should roll back to Friday Jan 5
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(pd.Timestamp("2024-01-06"))),
            ],
            other=ExchangeCalendarsHolidayCalendar([]),
            weekmask_periods=periods,
            roll_fn=roll_backward,
        )

        result = calendar.holidays()
        assert len(result) == 1
        assert result[0] == pd.Timestamp("2024-01-05")

    def test_roll_backward_across_period_boundary(self):
        """Test rolling backward from one period into another with different weekmask."""
        # Period 1: Jan 1-10, Mon-Fri open (Sat/Sun weekend)
        # Period 2: Jan 11-31, Mon-Sat open (only Sun weekend)
        periods = (
            WeekmaskPeriod(
                weekmask="1111100",  # Mon-Fri open
                start_date=pd.Timestamp("2024-01-01"),
                end_date=pd.Timestamp("2024-01-10"),
            ),
            WeekmaskPeriod(
                weekmask="1111110",  # Mon-Sat open
                start_date=pd.Timestamp("2024-01-11"),
                end_date=pd.Timestamp("2024-01-31"),
            ),
        )

        # Holiday on Sunday Jan 14 (in period 2 where Sun is weekend)
        # Should roll: Jan 14 (Sun, weekend in period 2) -> Jan 13 (Sat, conflict)
        # -> Jan 12 (Fri, conflict) -> Jan 11 (Thu, conflict) -> Jan 10 (Wed, conflict)
        # -> Jan 9 (Tue, conflict) -> Jan 8 (Mon, conflict) -> Jan 7 (Sun, weekend in period 1)
        # -> Jan 6 (Sat, weekend in period 1) -> Jan 5
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(pd.Timestamp("2024-01-14"))),
            ],
            other=ExchangeCalendarsHolidayCalendar(
                rules=[
                    Holiday(name="Other 1", **date2args(pd.Timestamp("2024-01-13"))),
                    Holiday(name="Other 2", **date2args(pd.Timestamp("2024-01-12"))),
                    Holiday(name="Other 3", **date2args(pd.Timestamp("2024-01-11"))),
                    Holiday(name="Other 4", **date2args(pd.Timestamp("2024-01-10"))),
                    Holiday(name="Other 5", **date2args(pd.Timestamp("2024-01-09"))),
                    Holiday(name="Other 6", **date2args(pd.Timestamp("2024-01-08"))),
                ]
            ),
            weekmask_periods=periods,
            roll_fn=roll_backward,
        )

        result = calendar.holidays()
        assert len(result) == 1
        assert result[0] == pd.Timestamp("2024-01-5")

    def test_roll_forward_across_period_boundary(self):
        """Test rolling forward from one period into another with different weekmask."""
        # Period 1: Jan 1-10, Mon-Fri open (Sat/Sun weekend)
        # Period 2: Jan 11-31, Mon-Sat open (only Sun weekend)
        periods = (
            WeekmaskPeriod(
                weekmask="1111100",  # Mon-Fri open
                start_date=pd.Timestamp("2024-01-01"),
                end_date=pd.Timestamp("2024-01-10"),
            ),
            WeekmaskPeriod(
                weekmask="1111110",  # Mon-Sat open
                start_date=pd.Timestamp("2024-01-11"),
                end_date=pd.Timestamp("2024-01-31"),
            ),
        )

        # Holiday on Sat Jan 6 (in period 1 where Sat is weekend)
        # With conflict on Jan 5, rolls forward to Jan 6 (Sat, weekend in period 1)
        # Should roll: Jan 6 (Sat, weekend in period 1) -> Jan 7 (Sun, weekend in period 1)
        # -> Jan 8 (Mon, conflict) -> Jan 9 (Tue, conflict) -> Jan 10 (Wed, conflict)
        # -> Jan 11 (Thu, conflict) -> Jan 12 (Fri, conflict) -> Jan 13
        calendar = AdjustedHolidayCalendar(
            rules=[
                Holiday(name=HOLIDAY, **date2args(pd.Timestamp("2024-01-06"))),
            ],
            other=ExchangeCalendarsHolidayCalendar(
                rules=[
                    Holiday(name="Other 1", **date2args(pd.Timestamp("2024-01-08"))),
                    Holiday(name="Other 2", **date2args(pd.Timestamp("2024-01-09"))),
                    Holiday(name="Other 3", **date2args(pd.Timestamp("2024-01-10"))),
                    Holiday(name="Other 4", **date2args(pd.Timestamp("2024-01-11"))),
                    Holiday(name="Other 5", **date2args(pd.Timestamp("2024-01-12"))),
                ]
            ),
            weekmask_periods=periods,
            roll_fn=roll_forward,
        )

        result = calendar.holidays()
        assert len(result) == 1
        # Jan 5 (conflict) -> Jan 6 (Sat, weekend) -> Jan 7 (Sun, weekend) -> Jan 8 (Mon, open)
        assert result[0] == pd.Timestamp("2024-01-13")
