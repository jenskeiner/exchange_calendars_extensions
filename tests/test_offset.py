import pandas as pd

from exchange_calendars_extensions.offset import get_third_day_of_week_in_month_offset_class, \
    get_last_day_of_month_offset_class


def test_get_third_day_of_week_in_month_offset_class():
    assert get_third_day_of_week_in_month_offset_class(3, 1)().holiday(2020) == pd.Timestamp('2020-01-16 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(4, 1)().holiday(2020) == pd.Timestamp('2020-01-17 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(3, 2)().holiday(2020) == pd.Timestamp('2020-02-20 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(4, 2)().holiday(2020) == pd.Timestamp('2020-02-21 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(3, 3)().holiday(2020) == pd.Timestamp('2020-03-19 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(4, 3)().holiday(2020) == pd.Timestamp('2020-03-20 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(3, 4)().holiday(2020) == pd.Timestamp('2020-04-16 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(4, 4)().holiday(2020) == pd.Timestamp('2020-04-17 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(3, 5)().holiday(2020) == pd.Timestamp('2020-05-21 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(4, 5)().holiday(2020) == pd.Timestamp('2020-05-15 00:00:00').date()
    assert get_third_day_of_week_in_month_offset_class(3, 6)().holiday(2020) == pd.Timestamp("2020-06-18 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(4, 6)().holiday(2020) == pd.Timestamp("2020-06-19 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(3, 7)().holiday(2020) == pd.Timestamp("2020-07-16 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(4, 7)().holiday(2020) == pd.Timestamp("2020-07-17 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(3, 8)().holiday(2020) == pd.Timestamp("2020-08-20 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(4, 8)().holiday(2020) == pd.Timestamp("2020-08-21 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(3, 9)().holiday(2020) == pd.Timestamp("2020-09-17 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(4, 9)().holiday(2020) == pd.Timestamp("2020-09-18 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(3, 10)().holiday(2020) == pd.Timestamp("2020-10-15 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(4, 10)().holiday(2020) == pd.Timestamp("2020-10-16 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(3, 11)().holiday(2020) == pd.Timestamp("2020-11-19 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(4, 11)().holiday(2020) == pd.Timestamp("2020-11-20 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(3, 12)().holiday(2020) == pd.Timestamp("2020-12-17 00:00:00").date()
    assert get_third_day_of_week_in_month_offset_class(4, 12)().holiday(2020) == pd.Timestamp("2020-12-18 00:00:00").date()


def test_get_last_day_of_month_offset_class():
    assert get_last_day_of_month_offset_class(1)().holiday(2020) == pd.Timestamp("2020-01-31 00:00:00").date()
    assert get_last_day_of_month_offset_class(2)().holiday(2020) == pd.Timestamp("2020-02-29 00:00:00").date()
    assert get_last_day_of_month_offset_class(3)().holiday(2020) == pd.Timestamp("2020-03-31 00:00:00").date()
    assert get_last_day_of_month_offset_class(4)().holiday(2020) == pd.Timestamp("2020-04-30 00:00:00").date()
    assert get_last_day_of_month_offset_class(5)().holiday(2020) == pd.Timestamp("2020-05-31 00:00:00").date()
    assert get_last_day_of_month_offset_class(6)().holiday(2020) == pd.Timestamp("2020-06-30 00:00:00").date()
    assert get_last_day_of_month_offset_class(7)().holiday(2020) == pd.Timestamp("2020-07-31 00:00:00").date()
    assert get_last_day_of_month_offset_class(8)().holiday(2020) == pd.Timestamp("2020-08-31 00:00:00").date()
    assert get_last_day_of_month_offset_class(9)().holiday(2020) == pd.Timestamp("2020-09-30 00:00:00").date()
    assert get_last_day_of_month_offset_class(10)().holiday(2020) == pd.Timestamp("2020-10-31 00:00:00").date()
    assert get_last_day_of_month_offset_class(11)().holiday(2020) == pd.Timestamp("2020-11-30 00:00:00").date()
    assert get_last_day_of_month_offset_class(12)().holiday(2020) == pd.Timestamp("2020-12-31 00:00:00").date()
