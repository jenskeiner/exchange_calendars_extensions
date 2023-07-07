import pandas as pd
import pytest

from exchange_calendars_extensions.util import get_day_of_week_name, get_month_name, third_day_of_week_in_month, \
    last_day_in_month


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
        assert third_day_of_week_in_month(0, 1, 2023) == pd.Timestamp("2023-01-16").date()
        assert third_day_of_week_in_month(0, 2, 2023) == pd.Timestamp("2023-02-20").date()
        assert third_day_of_week_in_month(0, 3, 2023) == pd.Timestamp("2023-03-20").date()
        assert third_day_of_week_in_month(0, 4, 2023) == pd.Timestamp("2023-04-17").date()
        assert third_day_of_week_in_month(0, 5, 2023) == pd.Timestamp("2023-05-15").date()
        assert third_day_of_week_in_month(0, 6, 2023) == pd.Timestamp("2023-06-19").date()
        assert third_day_of_week_in_month(0, 7, 2023) == pd.Timestamp("2023-07-17").date()
        assert third_day_of_week_in_month(0, 8, 2023) == pd.Timestamp("2023-08-21").date()
        assert third_day_of_week_in_month(0, 9, 2023) == pd.Timestamp("2023-09-18").date()
        assert third_day_of_week_in_month(0, 10, 2023) == pd.Timestamp("2023-10-16").date()
        assert third_day_of_week_in_month(0, 11, 2023) == pd.Timestamp("2023-11-20").date()
        assert third_day_of_week_in_month(0, 12, 2023) == pd.Timestamp("2023-12-18").date()

        # Tuesdays.
        assert third_day_of_week_in_month(1, 1, 2023) == pd.Timestamp("2023-01-17").date()
        assert third_day_of_week_in_month(1, 2, 2023) == pd.Timestamp("2023-02-21").date()
        assert third_day_of_week_in_month(1, 3, 2023) == pd.Timestamp("2023-03-21").date()
        assert third_day_of_week_in_month(1, 4, 2023) == pd.Timestamp("2023-04-18").date()
        assert third_day_of_week_in_month(1, 5, 2023) == pd.Timestamp("2023-05-16").date()
        assert third_day_of_week_in_month(1, 6, 2023) == pd.Timestamp("2023-06-20").date()
        assert third_day_of_week_in_month(1, 7, 2023) == pd.Timestamp("2023-07-18").date()
        assert third_day_of_week_in_month(1, 8, 2023) == pd.Timestamp("2023-08-15").date()
        assert third_day_of_week_in_month(1, 9, 2023) == pd.Timestamp("2023-09-19").date()
        assert third_day_of_week_in_month(1, 10, 2023) == pd.Timestamp("2023-10-17").date()
        assert third_day_of_week_in_month(1, 11, 2023) == pd.Timestamp("2023-11-21").date()
        assert third_day_of_week_in_month(1, 12, 2023) == pd.Timestamp("2023-12-19").date()

        # Wednesdays.
        assert third_day_of_week_in_month(2, 1, 2023) == pd.Timestamp("2023-01-18").date()
        assert third_day_of_week_in_month(2, 2, 2023) == pd.Timestamp("2023-02-15").date()
        assert third_day_of_week_in_month(2, 3, 2023) == pd.Timestamp("2023-03-15").date()
        assert third_day_of_week_in_month(2, 4, 2023) == pd.Timestamp("2023-04-19").date()
        assert third_day_of_week_in_month(2, 5, 2023) == pd.Timestamp("2023-05-17").date()
        assert third_day_of_week_in_month(2, 6, 2023) == pd.Timestamp("2023-06-21").date()
        assert third_day_of_week_in_month(2, 7, 2023) == pd.Timestamp("2023-07-19").date()
        assert third_day_of_week_in_month(2, 8, 2023) == pd.Timestamp("2023-08-16").date()
        assert third_day_of_week_in_month(2, 9, 2023) == pd.Timestamp("2023-09-20").date()
        assert third_day_of_week_in_month(2, 10, 2023) == pd.Timestamp("2023-10-18").date()
        assert third_day_of_week_in_month(2, 11, 2023) == pd.Timestamp("2023-11-15").date()
        assert third_day_of_week_in_month(2, 12, 2023) == pd.Timestamp("2023-12-20").date()

        # Thursdays.
        assert third_day_of_week_in_month(3, 1, 2023) == pd.Timestamp("2023-01-19").date()
        assert third_day_of_week_in_month(3, 2, 2023) == pd.Timestamp("2023-02-16").date()
        assert third_day_of_week_in_month(3, 3, 2023) == pd.Timestamp("2023-03-16").date()
        assert third_day_of_week_in_month(3, 4, 2023) == pd.Timestamp("2023-04-20").date()
        assert third_day_of_week_in_month(3, 5, 2023) == pd.Timestamp("2023-05-18").date()
        assert third_day_of_week_in_month(3, 6, 2023) == pd.Timestamp("2023-06-15").date()
        assert third_day_of_week_in_month(3, 7, 2023) == pd.Timestamp("2023-07-20").date()
        assert third_day_of_week_in_month(3, 8, 2023) == pd.Timestamp("2023-08-17").date()
        assert third_day_of_week_in_month(3, 9, 2023) == pd.Timestamp("2023-09-21").date()
        assert third_day_of_week_in_month(3, 10, 2023) == pd.Timestamp("2023-10-19").date()
        assert third_day_of_week_in_month(3, 11, 2023) == pd.Timestamp("2023-11-16").date()
        assert third_day_of_week_in_month(3, 12, 2023) == pd.Timestamp("2023-12-21").date()

        # Fridays.
        assert third_day_of_week_in_month(4, 1, 2023) == pd.Timestamp("2023-01-20").date()
        assert third_day_of_week_in_month(4, 2, 2023) == pd.Timestamp("2023-02-17").date()
        assert third_day_of_week_in_month(4, 3, 2023) == pd.Timestamp("2023-03-17").date()
        assert third_day_of_week_in_month(4, 4, 2023) == pd.Timestamp("2023-04-21").date()
        assert third_day_of_week_in_month(4, 5, 2023) == pd.Timestamp("2023-05-19").date()
        assert third_day_of_week_in_month(4, 6, 2023) == pd.Timestamp("2023-06-16").date()
        assert third_day_of_week_in_month(4, 7, 2023) == pd.Timestamp("2023-07-21").date()
        assert third_day_of_week_in_month(4, 8, 2023) == pd.Timestamp("2023-08-18").date()
        assert third_day_of_week_in_month(4, 9, 2023) == pd.Timestamp("2023-09-15").date()
        assert third_day_of_week_in_month(4, 10, 2023) == pd.Timestamp("2023-10-20").date()
        assert third_day_of_week_in_month(4, 11, 2023) == pd.Timestamp("2023-11-17").date()
        assert third_day_of_week_in_month(4, 12, 2023) == pd.Timestamp("2023-12-15").date()

        # Saturdays.
        assert third_day_of_week_in_month(5, 1, 2023) == pd.Timestamp("2023-01-21").date()
        assert third_day_of_week_in_month(5, 2, 2023) == pd.Timestamp("2023-02-18").date()
        assert third_day_of_week_in_month(5, 3, 2023) == pd.Timestamp("2023-03-18").date()
        assert third_day_of_week_in_month(5, 4, 2023) == pd.Timestamp("2023-04-15").date()
        assert third_day_of_week_in_month(5, 5, 2023) == pd.Timestamp("2023-05-20").date()
        assert third_day_of_week_in_month(5, 6, 2023) == pd.Timestamp("2023-06-17").date()
        assert third_day_of_week_in_month(5, 7, 2023) == pd.Timestamp("2023-07-15").date()
        assert third_day_of_week_in_month(5, 8, 2023) == pd.Timestamp("2023-08-19").date()
        assert third_day_of_week_in_month(5, 9, 2023) == pd.Timestamp("2023-09-16").date()
        assert third_day_of_week_in_month(5, 10, 2023) == pd.Timestamp("2023-10-21").date()
        assert third_day_of_week_in_month(5, 11, 2023) == pd.Timestamp("2023-11-18").date()
        assert third_day_of_week_in_month(5, 12, 2023) == pd.Timestamp("2023-12-16").date()

        # Sundays.
        assert third_day_of_week_in_month(6, 1, 2023) == pd.Timestamp("2023-01-15").date()
        assert third_day_of_week_in_month(6, 2, 2023) == pd.Timestamp("2023-02-19").date()
        assert third_day_of_week_in_month(6, 3, 2023) == pd.Timestamp("2023-03-19").date()
        assert third_day_of_week_in_month(6, 4, 2023) == pd.Timestamp("2023-04-16").date()
        assert third_day_of_week_in_month(6, 5, 2023) == pd.Timestamp("2023-05-21").date()
        assert third_day_of_week_in_month(6, 6, 2023) == pd.Timestamp("2023-06-18").date()
        assert third_day_of_week_in_month(6, 7, 2023) == pd.Timestamp("2023-07-16").date()
        assert third_day_of_week_in_month(6, 8, 2023) == pd.Timestamp("2023-08-20").date()
        assert third_day_of_week_in_month(6, 9, 2023) == pd.Timestamp("2023-09-17").date()
        assert third_day_of_week_in_month(6, 10, 2023) == pd.Timestamp("2023-10-15").date()
        assert third_day_of_week_in_month(6, 11, 2023) == pd.Timestamp("2023-11-19").date()
        assert third_day_of_week_in_month(6, 12, 2023) == pd.Timestamp("2023-12-17").date()

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
