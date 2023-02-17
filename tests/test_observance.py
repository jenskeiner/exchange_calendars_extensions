from exchange_calendars_extras.observance import get_roll_backward_observance
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday

import pandas as pd


def test_get_roll_backward_observance():
    # Define a holiday calendar with holidays on 2020-01-17 (Friday) to 2020-01-30 (Wednesday).
    calendar = HolidayCalendar([
        Holiday('Holiday', year=2020, month=1, day=17),
        Holiday('Holiday', year=2020, month=1, day=18),
        Holiday('Holiday', year=2020, month=1, day=19),
        Holiday('Holiday', year=2020, month=1, day=20),
        Holiday('Holiday', year=2020, month=1, day=21),
        Holiday('Holiday', year=2020, month=1, day=22),
        Holiday('Holiday', year=2020, month=1, day=23),
        Holiday('Holiday', year=2020, month=1, day=24),
        Holiday('Holiday', year=2020, month=1, day=25),
        Holiday('Holiday', year=2020, month=1, day=26),
        Holiday('Holiday', year=2020, month=1, day=27),
        Holiday('Holiday', year=2020, month=1, day=28),
        Holiday('Holiday', year=2020, month=1, day=29),
        Holiday('Holiday', year=2020, month=1, day=30),
    ])

    # Should not roll back.
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-16')) == pd.Timestamp('2020-01-16 00:00:00')

    # Should roll back to 2020-01-16 (Thursday).
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-17')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-18')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-19')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-20')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-21')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-22')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-23')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-24')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-25')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-26')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-27')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-28')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-29')) == pd.Timestamp('2020-01-16 00:00:00')
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-30')) == pd.Timestamp('2020-01-16 00:00:00')

    # Should not roll back.
    assert get_roll_backward_observance(calendar)(pd.Timestamp('2020-01-31')) == pd.Timestamp('2020-01-31 00:00:00')
