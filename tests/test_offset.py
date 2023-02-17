import pandas as pd

from exchange_calendars_extras.offset import get_third_day_of_week_in_month_offset_class


def test_get_third_day_of_week_in_month_offset_class():
    assert get_third_day_of_week_in_month_offset_class(3, 6)().holiday(2020) == pd.Timestamp("2020-06-18 00:00:00")
    assert get_third_day_of_week_in_month_offset_class(4, 6)().holiday(2020) == pd.Timestamp("2020-06-19 00:00:00")
