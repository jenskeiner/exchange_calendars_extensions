import pytest
import pandas as pd

from exchange_calendars_extras.util import get_day_of_week_name, get_month_name


def test_get_month_name():
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


def test_get_day_of_week_name():
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
