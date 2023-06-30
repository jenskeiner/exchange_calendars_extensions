from datetime import time

import pandas as pd
from exchange_calendars import get_calendar, ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.exchange_calendar_xlon import ChristmasEve, NewYearsEvePost2000
from pytz import timezone

from exchange_calendars_extensions.holiday_calendar import get_holiday_calendar_from_timestamps, \
    get_holiday_calendar_from_day_of_week, merge_calendars, get_holidays_calendar, get_special_closes_calendar, \
    get_special_opens_calendar, get_weekend_days_calendar, get_monthly_expiry_rules, get_quadruple_witching_rules, \
    get_last_day_of_month_rules


class TestHolidayCalendars:

    def test_get_holiday_calendar_from_timestamps(self):
        timestamps = [pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")]
        calendar = get_holiday_calendar_from_timestamps(timestamps)
        holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
        assert pd.Timestamp("2019-01-01") in holidays
        assert pd.Timestamp("2019-01-02") in holidays
        assert pd.Timestamp("2019-01-03") not in holidays
        assert pd.Timestamp("2019-01-04") not in holidays

    def test_get_holiday_calendar_from_day_of_week(self):
        calendar = get_holiday_calendar_from_day_of_week(0)
        holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
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
        calendar1 = get_holiday_calendar_from_timestamps([pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")])
        calendar2 = get_holiday_calendar_from_day_of_week(0)
        calendar = merge_calendars((calendar1, calendar2))
        holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
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
        calendar1 = get_holiday_calendar_from_timestamps([pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")])
        calendar2 = get_holiday_calendar_from_timestamps([pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-03")])
        calendar = merge_calendars((calendar1, calendar2))
        holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
        assert len(holidays) == 3
        assert pd.Timestamp("2019-01-01") in holidays
        assert pd.Timestamp("2019-01-02") in holidays
        assert pd.Timestamp("2019-01-03") in holidays
        assert pd.Timestamp("2019-01-04") not in holidays

    def test_get_holidays_calendar(self):
        calendar = get_calendar("XLON")
        holidays_calendar = get_holidays_calendar(calendar)
        holidays = holidays_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_holidays = pd.Series({
            pd.Timestamp("2020-01-01"): "New Year's Day",
            pd.Timestamp("2020-04-10"): "Good Friday",
            pd.Timestamp("2020-04-13"): "Easter Monday",
            pd.Timestamp("2020-05-08"): "ad-hoc holiday",
            pd.Timestamp("2020-05-25"): "Spring Bank Holiday",
            pd.Timestamp("2020-08-31"): "Summer Bank Holiday",
            pd.Timestamp("2020-12-25"): "Christmas",
            pd.Timestamp("2020-12-26"): "Boxing Day",
            pd.Timestamp("2020-12-28"): "Weekend Boxing Day",
        })
        assert holidays.compare(expected_holidays).empty

    def test_get_special_closes_calendar(self):

        class TestCalendar(ExchangeCalendar):
            regular_early_close = time(12, 30)
            name = "TEST"
            tz = timezone("Europe/London")
            open_times = ((None, time(8)),)
            close_times = ((None, time(16, 30)),)

            @property
            def regular_holidays(self): return HolidayCalendar([])

            @property
            def adhoc_holidays(self): return []

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
                    (time(11, 30), 0)  # Monday
                ]

            @property
            def special_closes_adhoc(self):
                return [
                    (
                        self.regular_early_close,
                        pd.DatetimeIndex([
                            pd.Timestamp("2020-01-08"),
                            pd.Timestamp("2020-08-12"),
                        ])
                    )
                ]

            ...

        calendar = TestCalendar()
        special_closes_calendar = get_special_closes_calendar(calendar)
        special_closes = special_closes_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_special_closes = pd.Series({
            pd.Timestamp("2020-01-06"): "special close",
            pd.Timestamp("2020-01-08"): "ad-hoc special close",
            pd.Timestamp("2020-01-13"): "special close",
            pd.Timestamp("2020-01-20"): "special close",
            pd.Timestamp("2020-01-27"): "special close",
            pd.Timestamp("2020-02-03"): "special close",
            pd.Timestamp("2020-02-10"): "special close",
            pd.Timestamp("2020-02-17"): "special close",
            pd.Timestamp("2020-02-24"): "special close",
            pd.Timestamp("2020-03-02"): "special close",
            pd.Timestamp("2020-03-09"): "special close",
            pd.Timestamp("2020-03-16"): "special close",
            pd.Timestamp("2020-03-23"): "special close",
            pd.Timestamp("2020-03-30"): "special close",
            pd.Timestamp("2020-04-06"): "special close",
            pd.Timestamp("2020-04-13"): "special close",
            pd.Timestamp("2020-04-20"): "special close",
            pd.Timestamp("2020-04-27"): "special close",
            pd.Timestamp("2020-05-04"): "special close",
            pd.Timestamp("2020-05-11"): "special close",
            pd.Timestamp("2020-05-18"): "special close",
            pd.Timestamp("2020-05-25"): "special close",
            pd.Timestamp("2020-06-01"): "special close",
            pd.Timestamp("2020-06-08"): "special close",
            pd.Timestamp("2020-06-15"): "special close",
            pd.Timestamp("2020-06-22"): "special close",
            pd.Timestamp("2020-06-29"): "special close",
            pd.Timestamp("2020-07-06"): "special close",
            pd.Timestamp("2020-07-13"): "special close",
            pd.Timestamp("2020-07-20"): "special close",
            pd.Timestamp("2020-07-27"): "special close",
            pd.Timestamp("2020-08-03"): "special close",
            pd.Timestamp("2020-08-10"): "special close",
            pd.Timestamp("2020-08-12"): "ad-hoc special close",
            pd.Timestamp("2020-08-17"): "special close",
            pd.Timestamp("2020-08-24"): "special close",
            pd.Timestamp("2020-08-31"): "special close",
            pd.Timestamp("2020-09-07"): "special close",
            pd.Timestamp("2020-09-14"): "special close",
            pd.Timestamp("2020-09-21"): "special close",
            pd.Timestamp("2020-09-28"): "special close",
            pd.Timestamp("2020-10-05"): "special close",
            pd.Timestamp("2020-10-12"): "special close",
            pd.Timestamp("2020-10-19"): "special close",
            pd.Timestamp("2020-10-26"): "special close",
            pd.Timestamp("2020-11-02"): "special close",
            pd.Timestamp("2020-11-09"): "special close",
            pd.Timestamp("2020-11-16"): "special close",
            pd.Timestamp("2020-11-23"): "special close",
            pd.Timestamp("2020-11-30"): "special close",
            pd.Timestamp("2020-12-07"): "special close",
            pd.Timestamp("2020-12-14"): "special close",
            pd.Timestamp("2020-12-21"): "special close",
            pd.Timestamp("2020-12-24"): "Christmas Eve",
            pd.Timestamp("2020-12-28"): "special close",
            pd.Timestamp("2020-12-31"): "New Year's Eve",
        })
        assert special_closes.compare(expected_special_closes).empty

    def test_get_special_opens_calendar(self):

        class TestCalendar(ExchangeCalendar):
            regular_late_open = time(10, 30)
            name = "TEST"
            tz = timezone("Europe/London")
            open_times = ((None, time(8)),)
            close_times = ((None, time(16, 30)),)

            @property
            def regular_holidays(self): return HolidayCalendar([])

            @property
            def adhoc_holidays(self): return []

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
                    (time(11, 30), 0)  # Monday
                ]

            @property
            def special_opens_adhoc(self):
                return [
                    (
                        self.regular_late_open,
                        pd.DatetimeIndex([
                            pd.Timestamp("2020-01-08"),
                            pd.Timestamp("2020-08-12"),
                        ])
                    )
                ]

            ...

        calendar = TestCalendar()
        special_opens_calendar = get_special_opens_calendar(calendar)
        special_opens = special_opens_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_special_opens = pd.Series({
            pd.Timestamp("2020-01-06"): "special open",
            pd.Timestamp("2020-01-08"): "ad-hoc special open",
            pd.Timestamp("2020-01-13"): "special open",
            pd.Timestamp("2020-01-20"): "special open",
            pd.Timestamp("2020-01-27"): "special open",
            pd.Timestamp("2020-02-03"): "special open",
            pd.Timestamp("2020-02-10"): "special open",
            pd.Timestamp("2020-02-17"): "special open",
            pd.Timestamp("2020-02-24"): "special open",
            pd.Timestamp("2020-03-02"): "special open",
            pd.Timestamp("2020-03-09"): "special open",
            pd.Timestamp("2020-03-16"): "special open",
            pd.Timestamp("2020-03-23"): "special open",
            pd.Timestamp("2020-03-30"): "special open",
            pd.Timestamp("2020-04-06"): "special open",
            pd.Timestamp("2020-04-13"): "special open",
            pd.Timestamp("2020-04-20"): "special open",
            pd.Timestamp("2020-04-27"): "special open",
            pd.Timestamp("2020-05-04"): "special open",
            pd.Timestamp("2020-05-11"): "special open",
            pd.Timestamp("2020-05-18"): "special open",
            pd.Timestamp("2020-05-25"): "special open",
            pd.Timestamp("2020-06-01"): "special open",
            pd.Timestamp("2020-06-08"): "special open",
            pd.Timestamp("2020-06-15"): "special open",
            pd.Timestamp("2020-06-22"): "special open",
            pd.Timestamp("2020-06-29"): "special open",
            pd.Timestamp("2020-07-06"): "special open",
            pd.Timestamp("2020-07-13"): "special open",
            pd.Timestamp("2020-07-20"): "special open",
            pd.Timestamp("2020-07-27"): "special open",
            pd.Timestamp("2020-08-03"): "special open",
            pd.Timestamp("2020-08-10"): "special open",
            pd.Timestamp("2020-08-12"): "ad-hoc special open",
            pd.Timestamp("2020-08-17"): "special open",
            pd.Timestamp("2020-08-24"): "special open",
            pd.Timestamp("2020-08-31"): "special open",
            pd.Timestamp("2020-09-07"): "special open",
            pd.Timestamp("2020-09-14"): "special open",
            pd.Timestamp("2020-09-21"): "special open",
            pd.Timestamp("2020-09-28"): "special open",
            pd.Timestamp("2020-10-05"): "special open",
            pd.Timestamp("2020-10-12"): "special open",
            pd.Timestamp("2020-10-19"): "special open",
            pd.Timestamp("2020-10-26"): "special open",
            pd.Timestamp("2020-11-02"): "special open",
            pd.Timestamp("2020-11-09"): "special open",
            pd.Timestamp("2020-11-16"): "special open",
            pd.Timestamp("2020-11-23"): "special open",
            pd.Timestamp("2020-11-30"): "special open",
            pd.Timestamp("2020-12-07"): "special open",
            pd.Timestamp("2020-12-14"): "special open",
            pd.Timestamp("2020-12-21"): "special open",
            pd.Timestamp("2020-12-24"): "Christmas Eve",
            pd.Timestamp("2020-12-28"): "special open",
            pd.Timestamp("2020-12-31"): "New Year's Eve",
        })
        assert special_opens.compare(expected_special_opens).empty

    def test_get_weekend_days_calendar(self):

        class TestCalendar(ExchangeCalendar):
            name = "TEST"
            tz = timezone("Europe/London")
            open_times = ((None, time(8)),)
            close_times = ((None, time(16, 30)),)
            weekmask = '1111010'

        calendar = TestCalendar()
        weekend_days_calendar = get_weekend_days_calendar(calendar)
        weekend_days = weekend_days_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-01-31"), return_name=True)
        expected_weekend_days = pd.Series({
            pd.Timestamp("2020-01-03"): "weekend day",
            pd.Timestamp("2020-01-05"): "weekend day",
            pd.Timestamp("2020-01-10"): "weekend day",
            pd.Timestamp("2020-01-12"): "weekend day",
            pd.Timestamp("2020-01-17"): "weekend day",
            pd.Timestamp("2020-01-19"): "weekend day",
            pd.Timestamp("2020-01-24"): "weekend day",
            pd.Timestamp("2020-01-26"): "weekend day",
            pd.Timestamp("2020-01-31"): "weekend day",
        })

        assert weekend_days.compare(expected_weekend_days).empty

    def test_get_monthly_expiry_calendar(self):

        # Test plain vanilla calendar without any special days or close days that may fall onto the same days as monthly
        # expiry.

        monthly_expiry_calendar = HolidayCalendar(rules=get_monthly_expiry_rules(day_of_week=4))
        monthly_expiry = monthly_expiry_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_monthly_expiry = pd.Series({
            pd.Timestamp("2020-01-17"): "monthly expiry",
            pd.Timestamp("2020-02-21"): "monthly expiry",
            pd.Timestamp("2020-04-17"): "monthly expiry",
            pd.Timestamp("2020-05-15"): "monthly expiry",
            pd.Timestamp("2020-07-17"): "monthly expiry",
            pd.Timestamp("2020-08-21"): "monthly expiry",
            pd.Timestamp("2020-10-16"): "monthly expiry",
            pd.Timestamp("2020-11-20"): "monthly expiry",
        })

        assert monthly_expiry.compare(expected_monthly_expiry).empty

        # Test calendar with identity observance.
        monthly_expiry_calendar = HolidayCalendar(rules=get_monthly_expiry_rules(day_of_week=4, observance=lambda x: x))
        monthly_expiry = monthly_expiry_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_monthly_expiry = pd.Series({
            pd.Timestamp("2020-01-17"): "monthly expiry",
            pd.Timestamp("2020-02-21"): "monthly expiry",
            pd.Timestamp("2020-04-17"): "monthly expiry",
            pd.Timestamp("2020-05-15"): "monthly expiry",
            pd.Timestamp("2020-07-17"): "monthly expiry",
            pd.Timestamp("2020-08-21"): "monthly expiry",
            pd.Timestamp("2020-10-16"): "monthly expiry",
            pd.Timestamp("2020-11-20"): "monthly expiry",
        })

        assert monthly_expiry.compare(expected_monthly_expiry).empty

        # Test calendar with an observance that moves the holiday to the previous day.
        monthly_expiry_calendar = HolidayCalendar(rules=get_monthly_expiry_rules(day_of_week=4, observance=lambda x: x - pd.Timedelta(days=1)))
        monthly_expiry = monthly_expiry_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_monthly_expiry = pd.Series({
            pd.Timestamp("2020-01-16"): "monthly expiry",
            pd.Timestamp("2020-02-20"): "monthly expiry",
            pd.Timestamp("2020-04-16"): "monthly expiry",
            pd.Timestamp("2020-05-14"): "monthly expiry",
            pd.Timestamp("2020-07-16"): "monthly expiry",
            pd.Timestamp("2020-08-20"): "monthly expiry",
            pd.Timestamp("2020-10-15"): "monthly expiry",
            pd.Timestamp("2020-11-19"): "monthly expiry",
        })

        assert monthly_expiry.compare(expected_monthly_expiry).empty

    def test_get_quadruple_witching_calendar(self):

        # Test plain vanilla calendar without any special days or close days that may fall onto the same days as quarterly
        # expiry.
        quarterly_expiry_calendar = HolidayCalendar(rules=get_quadruple_witching_rules(day_of_week=4))
        quarterly_expiry = quarterly_expiry_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_quarterly_expiry = pd.Series({
            pd.Timestamp("2020-03-20"): "quarterly expiry",
            pd.Timestamp("2020-06-19"): "quarterly expiry",
            pd.Timestamp("2020-09-18"): "quarterly expiry",
            pd.Timestamp("2020-12-18"): "quarterly expiry",
        })

        assert quarterly_expiry.compare(expected_quarterly_expiry).empty

        # Test calendar with identity observance.
        quarterly_expiry_calendar = HolidayCalendar(rules=get_quadruple_witching_rules(day_of_week=4, observance=lambda x: x))
        quarterly_expiry = quarterly_expiry_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_quarterly_expiry = pd.Series({
            pd.Timestamp("2020-03-20"): "quarterly expiry",
            pd.Timestamp("2020-06-19"): "quarterly expiry",
            pd.Timestamp("2020-09-18"): "quarterly expiry",
            pd.Timestamp("2020-12-18"): "quarterly expiry",
        })

        assert quarterly_expiry.compare(expected_quarterly_expiry).empty

        # Test calendar with an observance that moves the holiday to the previous day.
        quarterly_expiry_calendar = HolidayCalendar(rules=get_quadruple_witching_rules(day_of_week=4, observance=lambda x: x - pd.Timedelta(days=1)))
        quarterly_expiry = quarterly_expiry_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_quarterly_expiry = pd.Series({
            pd.Timestamp("2020-03-19"): "quarterly expiry",
            pd.Timestamp("2020-06-18"): "quarterly expiry",
            pd.Timestamp("2020-09-17"): "quarterly expiry",
            pd.Timestamp("2020-12-17"): "quarterly expiry",
        })

        assert quarterly_expiry.compare(expected_quarterly_expiry).empty

    def test_get_last_day_of_month_calendar(self):
        # Test plain vanilla calendar that ignores any special days or close days, even weekends, that may fall onto the
        # same days.
        last_day_of_month_calendar = HolidayCalendar(rules=get_last_day_of_month_rules(name="last day of month"))
        last_day_of_month = last_day_of_month_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_last_day_of_month = pd.Series({
            pd.Timestamp("2020-01-31"): "last day of month",
            pd.Timestamp("2020-02-29"): "last day of month",
            pd.Timestamp("2020-03-31"): "last day of month",
            pd.Timestamp("2020-04-30"): "last day of month",
            pd.Timestamp("2020-05-31"): "last day of month",
            pd.Timestamp("2020-06-30"): "last day of month",
            pd.Timestamp("2020-07-31"): "last day of month",
            pd.Timestamp("2020-08-31"): "last day of month",
            pd.Timestamp("2020-09-30"): "last day of month",
            pd.Timestamp("2020-10-31"): "last day of month",
            pd.Timestamp("2020-11-30"): "last day of month",
            pd.Timestamp("2020-12-31"): "last day of month",
        })

        assert last_day_of_month.compare(expected_last_day_of_month).empty

        # Test calendar with an observance that moves the holiday to the previous day.
        last_day_of_month_calendar = HolidayCalendar(rules=get_last_day_of_month_rules(name="last day of month", observance=lambda x: x - pd.Timedelta(days=1)))
        last_day_of_month = last_day_of_month_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
        expected_last_day_of_month = pd.Series({
            pd.Timestamp("2020-01-30"): "last day of month",
            pd.Timestamp("2020-02-28"): "last day of month",
            pd.Timestamp("2020-03-30"): "last day of month",
            pd.Timestamp("2020-04-29"): "last day of month",
            pd.Timestamp("2020-05-30"): "last day of month",
            pd.Timestamp("2020-06-29"): "last day of month",
            pd.Timestamp("2020-07-30"): "last day of month",
            pd.Timestamp("2020-08-30"): "last day of month",
            pd.Timestamp("2020-09-29"): "last day of month",
            pd.Timestamp("2020-10-30"): "last day of month",
            pd.Timestamp("2020-11-29"): "last day of month",
            pd.Timestamp("2020-12-30"): "last day of month",
        })

        assert last_day_of_month.compare(expected_last_day_of_month).empty
