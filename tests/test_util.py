import pandas as pd
import pytest
from exchange_calendars import get_calendar

from exchange_calendars_extensions.util import (
    Weekmask,
    WeekmaskPeriod,
    find_interval,
    get_day_of_week_name,
    get_month_name,
    get_weekmask_periods,
    last_day_in_month,
    set_weekday,
    third_day_of_week_in_month,
)


class TestUtils:
    def test_get_month_name(self):
        assert get_month_name(1) == "January"
        assert get_month_name(2) == "February"
        assert get_month_name(3) == "March"
        assert get_month_name(4) == "April"
        assert get_month_name(5) == "May"
        assert get_month_name(6) == "June"
        assert get_month_name(7) == "July"
        assert get_month_name(8) == "August"
        assert get_month_name(9) == "September"
        assert get_month_name(10) == "October"
        assert get_month_name(11) == "November"
        assert get_month_name(12) == "December"
        with pytest.raises(ValueError):
            get_month_name(13)
        with pytest.raises(ValueError):
            get_month_name(0)
        with pytest.raises(ValueError):
            get_month_name(-1)

    def test_get_day_of_week_name(self):
        assert get_day_of_week_name(0) == "Monday"
        assert get_day_of_week_name(1) == "Tuesday"
        assert get_day_of_week_name(2) == "Wednesday"
        assert get_day_of_week_name(3) == "Thursday"
        assert get_day_of_week_name(4) == "Friday"
        assert get_day_of_week_name(5) == "Saturday"
        assert get_day_of_week_name(6) == "Sunday"
        with pytest.raises(ValueError):
            get_day_of_week_name(7)
        with pytest.raises(ValueError):
            get_day_of_week_name(-1)

    def test_third_day_of_week_in_month(self):
        # Mondays.
        assert (
            third_day_of_week_in_month(0, 1, 2023) == pd.Timestamp("2023-01-16").date()
        )
        assert (
            third_day_of_week_in_month(0, 2, 2023) == pd.Timestamp("2023-02-20").date()
        )
        assert (
            third_day_of_week_in_month(0, 3, 2023) == pd.Timestamp("2023-03-20").date()
        )
        assert (
            third_day_of_week_in_month(0, 4, 2023) == pd.Timestamp("2023-04-17").date()
        )
        assert (
            third_day_of_week_in_month(0, 5, 2023) == pd.Timestamp("2023-05-15").date()
        )
        assert (
            third_day_of_week_in_month(0, 6, 2023) == pd.Timestamp("2023-06-19").date()
        )
        assert (
            third_day_of_week_in_month(0, 7, 2023) == pd.Timestamp("2023-07-17").date()
        )
        assert (
            third_day_of_week_in_month(0, 8, 2023) == pd.Timestamp("2023-08-21").date()
        )
        assert (
            third_day_of_week_in_month(0, 9, 2023) == pd.Timestamp("2023-09-18").date()
        )
        assert (
            third_day_of_week_in_month(0, 10, 2023) == pd.Timestamp("2023-10-16").date()
        )
        assert (
            third_day_of_week_in_month(0, 11, 2023) == pd.Timestamp("2023-11-20").date()
        )
        assert (
            third_day_of_week_in_month(0, 12, 2023) == pd.Timestamp("2023-12-18").date()
        )

        # Tuesdays.
        assert (
            third_day_of_week_in_month(1, 1, 2023) == pd.Timestamp("2023-01-17").date()
        )
        assert (
            third_day_of_week_in_month(1, 2, 2023) == pd.Timestamp("2023-02-21").date()
        )
        assert (
            third_day_of_week_in_month(1, 3, 2023) == pd.Timestamp("2023-03-21").date()
        )
        assert (
            third_day_of_week_in_month(1, 4, 2023) == pd.Timestamp("2023-04-18").date()
        )
        assert (
            third_day_of_week_in_month(1, 5, 2023) == pd.Timestamp("2023-05-16").date()
        )
        assert (
            third_day_of_week_in_month(1, 6, 2023) == pd.Timestamp("2023-06-20").date()
        )
        assert (
            third_day_of_week_in_month(1, 7, 2023) == pd.Timestamp("2023-07-18").date()
        )
        assert (
            third_day_of_week_in_month(1, 8, 2023) == pd.Timestamp("2023-08-15").date()
        )
        assert (
            third_day_of_week_in_month(1, 9, 2023) == pd.Timestamp("2023-09-19").date()
        )
        assert (
            third_day_of_week_in_month(1, 10, 2023) == pd.Timestamp("2023-10-17").date()
        )
        assert (
            third_day_of_week_in_month(1, 11, 2023) == pd.Timestamp("2023-11-21").date()
        )
        assert (
            third_day_of_week_in_month(1, 12, 2023) == pd.Timestamp("2023-12-19").date()
        )

        # Wednesdays.
        assert (
            third_day_of_week_in_month(2, 1, 2023) == pd.Timestamp("2023-01-18").date()
        )
        assert (
            third_day_of_week_in_month(2, 2, 2023) == pd.Timestamp("2023-02-15").date()
        )
        assert (
            third_day_of_week_in_month(2, 3, 2023) == pd.Timestamp("2023-03-15").date()
        )
        assert (
            third_day_of_week_in_month(2, 4, 2023) == pd.Timestamp("2023-04-19").date()
        )
        assert (
            third_day_of_week_in_month(2, 5, 2023) == pd.Timestamp("2023-05-17").date()
        )
        assert (
            third_day_of_week_in_month(2, 6, 2023) == pd.Timestamp("2023-06-21").date()
        )
        assert (
            third_day_of_week_in_month(2, 7, 2023) == pd.Timestamp("2023-07-19").date()
        )
        assert (
            third_day_of_week_in_month(2, 8, 2023) == pd.Timestamp("2023-08-16").date()
        )
        assert (
            third_day_of_week_in_month(2, 9, 2023) == pd.Timestamp("2023-09-20").date()
        )
        assert (
            third_day_of_week_in_month(2, 10, 2023) == pd.Timestamp("2023-10-18").date()
        )
        assert (
            third_day_of_week_in_month(2, 11, 2023) == pd.Timestamp("2023-11-15").date()
        )
        assert (
            third_day_of_week_in_month(2, 12, 2023) == pd.Timestamp("2023-12-20").date()
        )

        # Thursdays.
        assert (
            third_day_of_week_in_month(3, 1, 2023) == pd.Timestamp("2023-01-19").date()
        )
        assert (
            third_day_of_week_in_month(3, 2, 2023) == pd.Timestamp("2023-02-16").date()
        )
        assert (
            third_day_of_week_in_month(3, 3, 2023) == pd.Timestamp("2023-03-16").date()
        )
        assert (
            third_day_of_week_in_month(3, 4, 2023) == pd.Timestamp("2023-04-20").date()
        )
        assert (
            third_day_of_week_in_month(3, 5, 2023) == pd.Timestamp("2023-05-18").date()
        )
        assert (
            third_day_of_week_in_month(3, 6, 2023) == pd.Timestamp("2023-06-15").date()
        )
        assert (
            third_day_of_week_in_month(3, 7, 2023) == pd.Timestamp("2023-07-20").date()
        )
        assert (
            third_day_of_week_in_month(3, 8, 2023) == pd.Timestamp("2023-08-17").date()
        )
        assert (
            third_day_of_week_in_month(3, 9, 2023) == pd.Timestamp("2023-09-21").date()
        )
        assert (
            third_day_of_week_in_month(3, 10, 2023) == pd.Timestamp("2023-10-19").date()
        )
        assert (
            third_day_of_week_in_month(3, 11, 2023) == pd.Timestamp("2023-11-16").date()
        )
        assert (
            third_day_of_week_in_month(3, 12, 2023) == pd.Timestamp("2023-12-21").date()
        )

        # Fridays.
        assert (
            third_day_of_week_in_month(4, 1, 2023) == pd.Timestamp("2023-01-20").date()
        )
        assert (
            third_day_of_week_in_month(4, 2, 2023) == pd.Timestamp("2023-02-17").date()
        )
        assert (
            third_day_of_week_in_month(4, 3, 2023) == pd.Timestamp("2023-03-17").date()
        )
        assert (
            third_day_of_week_in_month(4, 4, 2023) == pd.Timestamp("2023-04-21").date()
        )
        assert (
            third_day_of_week_in_month(4, 5, 2023) == pd.Timestamp("2023-05-19").date()
        )
        assert (
            third_day_of_week_in_month(4, 6, 2023) == pd.Timestamp("2023-06-16").date()
        )
        assert (
            third_day_of_week_in_month(4, 7, 2023) == pd.Timestamp("2023-07-21").date()
        )
        assert (
            third_day_of_week_in_month(4, 8, 2023) == pd.Timestamp("2023-08-18").date()
        )
        assert (
            third_day_of_week_in_month(4, 9, 2023) == pd.Timestamp("2023-09-15").date()
        )
        assert (
            third_day_of_week_in_month(4, 10, 2023) == pd.Timestamp("2023-10-20").date()
        )
        assert (
            third_day_of_week_in_month(4, 11, 2023) == pd.Timestamp("2023-11-17").date()
        )
        assert (
            third_day_of_week_in_month(4, 12, 2023) == pd.Timestamp("2023-12-15").date()
        )

        # Saturdays.
        assert (
            third_day_of_week_in_month(5, 1, 2023) == pd.Timestamp("2023-01-21").date()
        )
        assert (
            third_day_of_week_in_month(5, 2, 2023) == pd.Timestamp("2023-02-18").date()
        )
        assert (
            third_day_of_week_in_month(5, 3, 2023) == pd.Timestamp("2023-03-18").date()
        )
        assert (
            third_day_of_week_in_month(5, 4, 2023) == pd.Timestamp("2023-04-15").date()
        )
        assert (
            third_day_of_week_in_month(5, 5, 2023) == pd.Timestamp("2023-05-20").date()
        )
        assert (
            third_day_of_week_in_month(5, 6, 2023) == pd.Timestamp("2023-06-17").date()
        )
        assert (
            third_day_of_week_in_month(5, 7, 2023) == pd.Timestamp("2023-07-15").date()
        )
        assert (
            third_day_of_week_in_month(5, 8, 2023) == pd.Timestamp("2023-08-19").date()
        )
        assert (
            third_day_of_week_in_month(5, 9, 2023) == pd.Timestamp("2023-09-16").date()
        )
        assert (
            third_day_of_week_in_month(5, 10, 2023) == pd.Timestamp("2023-10-21").date()
        )
        assert (
            third_day_of_week_in_month(5, 11, 2023) == pd.Timestamp("2023-11-18").date()
        )
        assert (
            third_day_of_week_in_month(5, 12, 2023) == pd.Timestamp("2023-12-16").date()
        )

        # Sundays.
        assert (
            third_day_of_week_in_month(6, 1, 2023) == pd.Timestamp("2023-01-15").date()
        )
        assert (
            third_day_of_week_in_month(6, 2, 2023) == pd.Timestamp("2023-02-19").date()
        )
        assert (
            third_day_of_week_in_month(6, 3, 2023) == pd.Timestamp("2023-03-19").date()
        )
        assert (
            third_day_of_week_in_month(6, 4, 2023) == pd.Timestamp("2023-04-16").date()
        )
        assert (
            third_day_of_week_in_month(6, 5, 2023) == pd.Timestamp("2023-05-21").date()
        )
        assert (
            third_day_of_week_in_month(6, 6, 2023) == pd.Timestamp("2023-06-18").date()
        )
        assert (
            third_day_of_week_in_month(6, 7, 2023) == pd.Timestamp("2023-07-16").date()
        )
        assert (
            third_day_of_week_in_month(6, 8, 2023) == pd.Timestamp("2023-08-20").date()
        )
        assert (
            third_day_of_week_in_month(6, 9, 2023) == pd.Timestamp("2023-09-17").date()
        )
        assert (
            third_day_of_week_in_month(6, 10, 2023) == pd.Timestamp("2023-10-15").date()
        )
        assert (
            third_day_of_week_in_month(6, 11, 2023) == pd.Timestamp("2023-11-19").date()
        )
        assert (
            third_day_of_week_in_month(6, 12, 2023) == pd.Timestamp("2023-12-17").date()
        )

    def test_last_day_in_month(self):
        # Regular year.
        assert last_day_in_month(1, 2023) == pd.Timestamp("2023-01-31").date()
        assert last_day_in_month(2, 2023) == pd.Timestamp("2023-02-28").date()
        assert last_day_in_month(3, 2023) == pd.Timestamp("2023-03-31").date()
        assert last_day_in_month(4, 2023) == pd.Timestamp("2023-04-30").date()
        assert last_day_in_month(5, 2023) == pd.Timestamp("2023-05-31").date()
        assert last_day_in_month(6, 2023) == pd.Timestamp("2023-06-30").date()
        assert last_day_in_month(7, 2023) == pd.Timestamp("2023-07-31").date()
        assert last_day_in_month(8, 2023) == pd.Timestamp("2023-08-31").date()
        assert last_day_in_month(9, 2023) == pd.Timestamp("2023-09-30").date()
        assert last_day_in_month(10, 2023) == pd.Timestamp("2023-10-31").date()
        assert last_day_in_month(11, 2023) == pd.Timestamp("2023-11-30").date()
        assert last_day_in_month(12, 2023) == pd.Timestamp("2023-12-31").date()

        # Leap year.
        assert last_day_in_month(1, 2020) == pd.Timestamp("2020-01-31").date()
        assert last_day_in_month(2, 2020) == pd.Timestamp("2020-02-29").date()
        assert last_day_in_month(3, 2020) == pd.Timestamp("2020-03-31").date()
        assert last_day_in_month(4, 2020) == pd.Timestamp("2020-04-30").date()
        assert last_day_in_month(5, 2020) == pd.Timestamp("2020-05-31").date()
        assert last_day_in_month(6, 2020) == pd.Timestamp("2020-06-30").date()
        assert last_day_in_month(7, 2020) == pd.Timestamp("2020-07-31").date()
        assert last_day_in_month(8, 2020) == pd.Timestamp("2020-08-31").date()
        assert last_day_in_month(9, 2020) == pd.Timestamp("2020-09-30").date()
        assert last_day_in_month(10, 2020) == pd.Timestamp("2020-10-31").date()
        assert last_day_in_month(11, 2020) == pd.Timestamp("2020-11-30").date()
        assert last_day_in_month(12, 2020) == pd.Timestamp("2020-12-31").date()

    def test_get_weekmask_periods_without_special_weekmasks(self):
        """Test get_weekmask_periods for calendars without special_weekmasks."""
        calendar = get_calendar("XLON")
        periods = get_weekmask_periods(calendar)

        assert len(periods) == 1
        assert periods[0].weekmask == WEEKMASK_DEFAULT
        assert periods[0].start_date is None
        assert periods[0].end_date is None

    def test_get_weekmask_periods_xtae(self):
        """Test get_weekmask_periods for XTAE which has a special weekmask from beginning."""
        calendar = get_calendar("XTAE")
        periods = get_weekmask_periods(calendar)

        assert len(periods) == 2
        assert periods[0].weekmask == "1111001"
        assert periods[0].start_date is None
        assert periods[0].end_date == pd.Timestamp("2026-01-04")

        assert periods[1].weekmask == WEEKMASK_DEFAULT
        assert periods[1].start_date == pd.Timestamp("2026-01-05")
        assert periods[1].end_date is None

    def test_get_weekmask_periods_xbom(self):
        """Test get_weekmask_periods for XBOM which has special weekmasks with gaps."""
        calendar = get_calendar("XBOM")
        periods = get_weekmask_periods(calendar)

        # Should have: default, special1, default gap, special2, default
        assert len(periods) == 5

        # First: default from beginning until first special weekmask
        assert periods[0].weekmask == WEEKMASK_DEFAULT
        assert periods[0].start_date is None
        assert periods[0].end_date == pd.Timestamp("2024-01-14")

        # Second: first special weekmask
        assert periods[1].weekmask == "1111110"
        assert periods[1].start_date == pd.Timestamp("2024-01-15")
        assert periods[1].end_date == pd.Timestamp("2024-01-21")

        # Third: default gap between special weekmasks
        assert periods[2].weekmask == WEEKMASK_DEFAULT
        assert periods[2].start_date == pd.Timestamp("2024-01-22")
        assert periods[2].end_date == pd.Timestamp("2025-01-26")

        # Fourth: second special weekmask
        assert periods[3].weekmask == "1111110"
        assert periods[3].start_date == pd.Timestamp("2025-01-27")
        assert periods[3].end_date == pd.Timestamp("2025-02-02")

        # Fifth: default from second special weekmask end onwards
        assert periods[4].weekmask == WEEKMASK_DEFAULT
        assert periods[4].start_date == pd.Timestamp("2025-02-03")
        assert periods[4].end_date is None

    def test_find_interval_with_none_start_date(self):
        """Test find_interval with None as the first start_date."""
        intervals = (
            (None, "value1"),
            (pd.Timestamp("2020-01-01"), "value2"),
            (pd.Timestamp("2021-01-01"), "value3"),
        )

        # Before first explicit date
        start, value = find_interval(intervals, pd.Timestamp("2019-06-15"))
        assert start is None
        assert value == "value1"

        # Exactly on first explicit date
        start, value = find_interval(intervals, pd.Timestamp("2020-01-01"))
        assert start == pd.Timestamp("2020-01-01")
        assert value == "value2"

    def test_find_interval_with_multiple_intervals(self):
        """Test find_interval with multiple intervals."""
        intervals = (
            (None, "early"),
            (pd.Timestamp("2020-01-01"), "middle1"),
            (pd.Timestamp("2021-01-01"), "middle2"),
            (pd.Timestamp("2022-01-01"), "late"),
        )

        # Test each interval
        assert find_interval(intervals, pd.Timestamp("2019-06-15")) == (None, "early")
        assert find_interval(intervals, pd.Timestamp("2020-06-15")) == (
            pd.Timestamp("2020-01-01"),
            "middle1",
        )
        assert find_interval(intervals, pd.Timestamp("2021-06-15")) == (
            pd.Timestamp("2021-01-01"),
            "middle2",
        )
        assert find_interval(intervals, pd.Timestamp("2022-06-15")) == (
            pd.Timestamp("2022-01-01"),
            "late",
        )

    def test_find_interval_edge_cases(self):
        """Test find_interval edge cases."""
        intervals = (
            (None, "value1"),
            (pd.Timestamp("2020-01-01"), "value2"),
        )

        # Timestamp just before boundary
        start, value = find_interval(intervals, pd.Timestamp("2019-12-31"))
        assert start is None
        assert value == "value1"

        # Timestamp on boundary
        start, value = find_interval(intervals, pd.Timestamp("2020-01-01"))
        assert start == pd.Timestamp("2020-01-01")
        assert value == "value2"

    def test_find_interval_empty_intervals_raises(self):
        """Test find_interval raises ValueError for empty intervals."""
        with pytest.raises(ValueError, match="intervals must not be empty"):
            find_interval((), pd.Timestamp("2020-01-01"))


WEEKMASK_DEFAULT: Weekmask = Weekmask("1111100")
WEEKMASK_ALT_1: Weekmask = Weekmask("0001111")
WEEKMASK_ALT_2: Weekmask = Weekmask("1110000")

SATURDAY_TS = pd.Timestamp("2024-01-13")
MONDAY_TS = pd.Timestamp("2024-01-15")

TESTDATA = [
    (True, SATURDAY_TS, "1111110"),
    (False, MONDAY_TS, "0111100"),
]

PERIOD_START_DEFAULT_TS = pd.Timestamp("2024-01-01")
PERIOD_END_DEFAULT_TS = pd.Timestamp("2024-01-31")


class TestSetWeekday:
    """Exhaustive tests for set_weekday covering all branches."""

    # -- Empty input --

    def test_empty_periods(self):
        """Empty periods tuple returns empty tuple."""
        result = set_weekday((), pd.Timestamp("2024-01-15"), True)
        assert result == ()

    # -- Period does not contain the date --

    @pytest.mark.parametrize("weekday", [False, True])
    def test_date_before_period(self, weekday: bool):
        """Date before period's start_date leaves period unchanged."""
        p = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=pd.Timestamp("2024-02-01"),
            end_date=pd.Timestamp("2024-02-28"),
        )
        result = set_weekday((p,), pd.Timestamp("2024-01-15"), weekday)
        assert result == (p,)

    @pytest.mark.parametrize("weekday", [False, True])
    def test_date_after_period(self, weekday: bool):
        """Date after period's end_date leaves period unchanged."""
        p = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=pd.Timestamp("2024-01-01"),
            end_date=pd.Timestamp("2024-01-31"),
        )
        result = set_weekday((p,), pd.Timestamp("2024-02-15"), weekday)
        assert result == (p,)

    # -- Period contains the date but weekmask already matches --

    @pytest.mark.parametrize(
        "weekday,date",
        [(False, pd.Timestamp("2024-01-13")), (True, pd.Timestamp("2024-01-15"))],
    )
    def test_day_already_set(self, weekday: bool, date: pd.Timestamp):
        """Date is a weekday (bit=1) and weekday=True; no change needed."""
        p = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=pd.Timestamp("2024-01-01"),
            end_date=pd.Timestamp("2024-01-31"),
        )
        result = set_weekday((p,), date, weekday)
        assert result == (p,)

    # -- Split: date in the middle of a bounded period (all 3 sub-periods non-empty) --

    @pytest.mark.parametrize("period_start", [PERIOD_START_DEFAULT_TS, None])
    @pytest.mark.parametrize("period_end", [PERIOD_END_DEFAULT_TS, None])
    @pytest.mark.parametrize(
        "weekday,date,weekmask",
        TESTDATA,
    )
    def test_split_middle_of_period(
        self,
        period_start: pd.Timestamp | None,
        period_end: pd.Timestamp | None,
        weekday: bool,
        date: pd.Timestamp,
        weekmask: Weekmask,
    ):
        """Setting weekday=False for a day that is currently 1, date in middle of bounded period."""
        p = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=period_start,
            end_date=period_end,
        )
        result = set_weekday((p,), date, weekday)
        assert len(result) == 3
        # p0: before the date
        assert result[0].start_date == period_start
        assert result[0].end_date == date + pd.Timedelta(days=-1)
        assert result[0].weekmask == WEEKMASK_DEFAULT
        # p1: the date itself
        assert result[1].start_date == date
        assert result[1].end_date == date
        assert result[1].weekmask == weekmask
        # p2: after the date
        assert result[2].start_date == date + pd.Timedelta(days=1)
        assert result[2].end_date == period_end
        assert result[2].weekmask == WEEKMASK_DEFAULT

    # -- Split: date == start_date of bounded period (p0 becomes empty) --

    @pytest.mark.parametrize("period_end", [PERIOD_END_DEFAULT_TS, None])
    @pytest.mark.parametrize(
        "weekday,date,weekmask",
        TESTDATA,
    )
    def test_split_at_start_of_period(
        self,
        period_end: pd.Timestamp | None,
        weekday: bool,
        date: pd.Timestamp,
        weekmask: Weekmask,
    ):
        """Date equals start_date: p0 is empty and filtered out, only p1 and p2 remain."""
        p = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=date,
            end_date=period_end,
        )
        # 2024-01-15 is Monday, weekmask[0]='1', set to False to trigger split
        result = set_weekday((p,), date, weekday)
        assert len(result) == 2
        # p1: the date itself
        assert result[0].start_date == date
        assert result[0].end_date == date
        assert result[0].weekmask == weekmask
        # p2: after the date
        assert result[1].start_date == date + pd.Timedelta(days=1)
        assert result[1].end_date == period_end
        assert result[1].weekmask == WEEKMASK_DEFAULT

    # -- Split: date == end_date of bounded period (p2 becomes empty) --

    @pytest.mark.parametrize("period_start", [PERIOD_START_DEFAULT_TS, None])
    @pytest.mark.parametrize(
        "weekday,date,weekmask",
        TESTDATA,
    )
    def test_split_at_end_of_period(
        self,
        period_start: pd.Timestamp | None,
        weekday: bool,
        date: pd.Timestamp,
        weekmask: Weekmask,
    ):
        """Date equals end_date: p2 is empty and filtered out, only p0 and p1 remain."""
        p = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=period_start,
            end_date=date,
        )
        # 2024-01-15 is Monday, weekmask[0]='1', set to False to trigger split
        result = set_weekday((p,), date, weekday)
        assert len(result) == 2
        # p0: before the date
        assert result[0].start_date == period_start
        assert result[0].end_date == date + pd.Timedelta(days=-1)
        assert result[0].weekmask == WEEKMASK_DEFAULT
        # p1: the date itself
        assert result[1].start_date == date
        assert result[1].end_date == date
        assert result[1].weekmask == weekmask

    # -- Split: single-day period where date == start_date == end_date (p0 and p2 both empty) --

    @pytest.mark.parametrize(
        "weekday,date,weekmask",
        TESTDATA,
    )
    def test_split_single_day_period(
        self, weekday: bool, date: pd.Timestamp, weekmask: Weekmask
    ):
        """Period is a single day equal to the date: p0 and p2 are empty, only p1 remains."""
        p = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=date,
            end_date=date,
        )
        # 2024-01-15 is Monday, weekmask[0]='1', set to False
        result = set_weekday((p,), date, weekday)
        assert len(result) == 1
        assert result[0].start_date == date
        assert result[0].end_date == date
        assert result[0].weekmask == weekmask

    # -- Multiple periods: only the matching one is split --

    @pytest.mark.parametrize("period_start", [PERIOD_START_DEFAULT_TS, None])
    @pytest.mark.parametrize("period_end", [PERIOD_END_DEFAULT_TS, None])
    @pytest.mark.parametrize(
        "weekday,date,weekmask",
        TESTDATA,
    )
    def test_multiple_periods_only_matching_split(
        self,
        period_start: pd.Timestamp | None,
        period_end: pd.Timestamp | None,
        weekday: bool,
        date: pd.Timestamp,
        weekmask: Weekmask,
    ):
        """With multiple periods, only the one containing the date is split."""
        split1 = pd.Timestamp("2024-01-07")
        split2 = pd.Timestamp("2024-01-23")
        p1 = WeekmaskPeriod(
            weekmask=WEEKMASK_ALT_1,
            start_date=period_start,
            end_date=split1,
        )
        p2 = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=split1 + pd.Timedelta(days=1),
            end_date=split2,
        )
        p3 = WeekmaskPeriod(
            weekmask=WEEKMASK_ALT_2,
            start_date=split2 + pd.Timedelta(days=1),
            end_date=period_end,
        )
        # 2024-01-22 is Monday, in p2
        result = set_weekday((p1, p2, p3), date, weekday)
        assert len(result) == 5
        # p1 unchanged
        assert result[0] == p1
        # p2 split into 3
        assert result[1].start_date == p2.start_date
        assert result[1].end_date == date + pd.Timedelta(days=-1)
        assert result[1].weekmask == WEEKMASK_DEFAULT
        assert result[2].start_date == date
        assert result[2].end_date == date
        assert result[2].weekmask == weekmask
        assert result[3].start_date == date + pd.Timedelta(days=1)
        assert result[3].end_date == split2
        assert result[3].weekmask == WEEKMASK_DEFAULT
        assert result[4] == p3

    @pytest.mark.parametrize("period_start", [PERIOD_START_DEFAULT_TS, None])
    @pytest.mark.parametrize("period_end", [PERIOD_END_DEFAULT_TS, None])
    @pytest.mark.parametrize(
        "weekday,date,weekmask",
        TESTDATA,
    )
    def test_periods_optimized(
        self,
        period_start: pd.Timestamp | None,
        period_end: pd.Timestamp | None,
        weekday: bool,
        date: pd.Timestamp,
        weekmask: Weekmask,
    ):
        """With multiple periods, only the one containing the date is split."""
        split1 = pd.Timestamp("2024-01-07")
        split2 = pd.Timestamp("2024-01-23")
        p1 = WeekmaskPeriod(
            weekmask=WEEKMASK_ALT_1,
            start_date=period_start,
            end_date=split1,
        )
        p2 = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=split1 + pd.Timedelta(days=1),
            end_date=split2,
        )
        p3 = WeekmaskPeriod(
            weekmask=WEEKMASK_ALT_2,
            start_date=split2 + pd.Timedelta(days=1),
            end_date=period_end,
        )
        # 2024-01-22 is Monday, in p2
        result = set_weekday((p1, p2, p3), date, weekday)
        assert len(result) == 5
        # p1 unchanged
        assert result[0] == p1
        # p2 split into 3
        assert result[1].start_date == p2.start_date
        assert result[1].end_date == date + pd.Timedelta(days=-1)
        assert result[1].weekmask == WEEKMASK_DEFAULT
        assert result[2].start_date == date
        assert result[2].end_date == date
        assert result[2].weekmask == weekmask
        assert result[3].start_date == date + pd.Timedelta(days=1)
        assert result[3].end_date == split2
        assert result[3].weekmask == WEEKMASK_DEFAULT
        assert result[4] == p3

        # Revert the change.
        result = set_weekday(result, date, not weekday)

        # Original intervals should be recovered.
        assert result == (p1, p2, p3)

    @pytest.mark.parametrize("period_start", [PERIOD_START_DEFAULT_TS, None])
    @pytest.mark.parametrize("period_end", [PERIOD_END_DEFAULT_TS, None])
    @pytest.mark.parametrize(
        "weekday,date,weekmask",
        TESTDATA,
    )
    def test_multiple_periods_none_matching(
        self,
        period_start: pd.Timestamp | None,
        period_end: pd.Timestamp | None,
        weekday: bool,
        date: pd.Timestamp,
        weekmask: Weekmask,
    ):
        """With multiple periods, none containing the date means all unchanged."""
        p1 = WeekmaskPeriod(
            weekmask=WEEKMASK_DEFAULT,
            start_date=period_start,
            end_date=date + pd.Timedelta(days=-1),
        )
        p2 = WeekmaskPeriod(
            weekmask=WEEKMASK_ALT_1,
            start_date=date + pd.Timedelta(days=1),
            end_date=period_end,
        )
        result = set_weekday((p1, p2), date, weekday)
        assert result == (p1, p2)
