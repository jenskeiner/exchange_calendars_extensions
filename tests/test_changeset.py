import datetime as dt
from typing import Union

import pandas as pd
import pytest
from pydantic import ValidationError, Field, validate_call
from typing_extensions import Annotated

from exchange_calendars_extensions import DayType
from exchange_calendars_extensions.changeset import ChangeSet, DaySpec, DaySpecWithTime


@validate_call
def to_day_spec(value: Annotated[Union[DaySpec, DaySpecWithTime, dict], Field(discriminator='type')]):
    return value


class TestChangeSet:
    def test_empty_changeset(self):
        cs = ChangeSet()
        assert len(cs) == 0

    @pytest.mark.parametrize(["day"], [
        ({'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'},),
        (DaySpec(**{'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'}),),
        ({'date': pd.Timestamp('2020-01-01'), 'type': DayType.HOLIDAY, 'name': 'Holiday'},),
        ({'date': pd.Timestamp('2020-01-01').date(), 'type': 'holiday', 'name': 'Holiday'},),
        ({'date': '2020-01-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'},),
        (DaySpecWithTime(**{'date': '2020-01-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'}),),
        ({'date': pd.Timestamp('2020-01-01'), 'type': DayType.SPECIAL_OPEN, 'name': 'Special Open', 'time': '10:00:00'},),
        ({'date': pd.Timestamp('2020-01-01').date(), 'type': 'special_open', 'name': 'Special Open', 'time': dt.time(10, 0)},),
        ({'date': '2020-01-01', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'},),
        (DaySpecWithTime(**{'date': '2020-01-01', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'}),),
        ({'date': pd.Timestamp('2020-01-01'), 'type': DayType.SPECIAL_CLOSE, 'name': 'Special Close', 'time': '16:00:00'},),
        ({'date': pd.Timestamp('2020-01-01').date(), 'type': 'special_close', 'name': 'Special Close', 'time': dt.time(16, 0)},),
        ({'date': '2020-01-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'},),
        (DaySpec(**{'date': '2020-01-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'}),),
        ({'date': pd.Timestamp('2020-01-01'), 'type': DayType.MONTHLY_EXPIRY, 'name': 'Monthly Expiry'},),
        ({'date': pd.Timestamp('2020-01-01').date(), 'type': 'monthly_expiry', 'name': 'Monthly Expiry'},),
        ({'date': '2020-01-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'},),
        (DaySpec(**{'date': '2020-01-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'}),),
        ({'date': pd.Timestamp('2020-01-01'), 'type': DayType.QUARTERLY_EXPIRY, 'name': 'Quarterly Expiry'},),
        ({'date': pd.Timestamp('2020-01-01').date(), 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'},),
    ])
    def test_add_valid_day(self, day: Union[DaySpec, DaySpecWithTime, dict]):
        # Empty changeset.
        cs = ChangeSet()

        # Add day.
        cs.add_day(day)

        # Check length.
        assert len(cs) == 1

        # Convert input to validated object, maybe.
        day = to_day_spec(day)

        # Get the only element from the list.
        day0 = cs.add[0]

        # Check it's identical to the input.
        assert day0 == day

    @pytest.mark.parametrize(["date"], [
        ("2020-01-01",),
        (pd.Timestamp("2020-01-01"),),
        (pd.Timestamp("2020-01-01").date(),),
    ])
    def test_remove_day(self, date):
        cs = ChangeSet()
        cs.remove_day(date)
        assert len(cs) == 1

        # Check given day type.
        assert cs.remove == [pd.Timestamp("2020-01-01")]

    @pytest.mark.parametrize(["date", "value"], [
        ('2020-01-01', {'type': 'holiday', 'name': 'Holiday'}),
        (pd.Timestamp('2020-01-01'), {'type': 'holiday', 'name': 'Holiday'}),
        (pd.Timestamp('2020-01-01').date(), {'type': 'holiday', 'name': 'Holiday'}),
        ('2020-01-01', {'type': 'special_open', 'name': 'Special Open', 'time': '10:00'}),
        (pd.Timestamp('2020-01-01'), {'type': 'special_open', 'name': 'Special Open', 'time': '10:00:00'}),
        (pd.Timestamp('2020-01-01').date(), {'type': 'special_open', 'name': 'Special Open', 'time': dt.time(10, 0)}),
        ('2020-01-01', {'type': 'special_close', 'name': 'Special Close', 'time': '16:00'}),
        (pd.Timestamp('2020-01-01'), {'type': 'special_close', 'name': 'Special Close', 'time': '16:00:00'}),
        (pd.Timestamp('2020-01-01').date(), {'type': 'special_close', 'name': 'Special Close', 'time': dt.time(16, 0)}),
        ('2020-01-01', {'type': 'monthly_expiry', 'name': 'Monthly Expiry'}),
        (pd.Timestamp('2020-01-01'), {'type': 'monthly_expiry', 'name': 'Monthly Expiry'}),
        (pd.Timestamp('2020-01-01').date(), {'type': 'monthly_expiry', 'name': 'Monthly Expiry'}),
        ('2020-01-01', {'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'}),
        (pd.Timestamp('2020-01-01'), {'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'}),
        (pd.Timestamp('2020-01-01').date(), {'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'}),
    ])
    def test_clear_day(self, date, value: dict):
        # Add day.
        cs = ChangeSet()
        cs.add_day({**value, 'date': date})
        assert len(cs) == 1

        # Clear day.
        cs.clear_day(date)
        assert len(cs) == 0

        # Remove day.
        cs.remove_day(date)
        assert len(cs) == 1

        # Clear day.
        cs.clear_day(date)
        assert len(cs) == 0

    def test_clear(self):
        cs = ChangeSet()
        cs.add_day({'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'})
        cs.add_day({'date': '2020-01-02', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'})
        cs.add_day({'date': '2020-01-03', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'})
        cs.add_day({'date': '2020-01-04', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'})
        cs.add_day({'date': '2020-01-05', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'})
        cs.remove_day('2020-01-06')
        cs.remove_day('2020-01-07')
        cs.remove_day('2020-01-08')
        cs.remove_day('2020-01-09')
        cs.remove_day('2020-01-10')

        assert len(cs) == 10

        cs.clear()

        assert not cs
        assert cs.add == []
        assert cs.remove == []

    @pytest.mark.parametrize(['date', 'value'], [
        ('2020-01-01', {'type': 'holiday', 'name': 'Holiday'},),
        ('2020-01-01', {'type': 'special_open', 'name': 'Special Open', 'time': '10:00'},),
        ('2020-01-01', {'type': 'special_close', 'name': 'Special Close', 'time': '16:00'},),
        ('2020-01-01', {'type': 'monthly_expiry', 'name': 'Monthly Expiry'},),
        ('2020-01-01', {'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'},),
    ])
    def test_add_remove_day_for_same_day_type(self, date, value):
        cs = ChangeSet()
        cs.add_day({**value, 'date': date})
        cs.remove_day(date)
        assert len(cs) == 2
        assert cs

    def test_add_same_day_twice(self):
        cs = ChangeSet()
        d = {'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'}
        cs.add_day(d)
        with pytest.raises(ValueError):
            cs.add_day({'date': '2020-01-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'})
        assert len(cs) == 1
        assert cs.add == [to_day_spec(d)]
        assert cs

    @pytest.mark.parametrize(['d', 'cs'], [
        ({'add': [{'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'}]},
         ChangeSet().add_day({'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'})),
        ({'add': [{'date': '2020-01-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'}]},
         ChangeSet().add_day({'date': '2020-01-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'})),
        ({'add': [{'date': '2020-01-01', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'}]},
         ChangeSet().add_day({'date': '2020-01-01', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'})),
        ({'add': [{'date': '2020-01-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'}]},
         ChangeSet().add_day({'date': '2020-01-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'})),
        ({'add': [{'date': '2020-01-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'}]},
         ChangeSet().add_day({'date': '2020-01-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'})),
        ({'remove': ['2020-01-01']},
         ChangeSet().remove_day('2020-01-01')),
        ({
             'add': [
                 {'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'},
                 {'date': '2020-02-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'},
                 {'date': '2020-03-01', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'},
                 {'date': '2020-04-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'},
                 {'date': '2020-05-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'},
             ],
             'remove': ['2020-01-02','2020-02-02','2020-03-02','2020-04-02','2020-05-02']
         },
         ChangeSet()
         .add_day({'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'})
         .remove_day('2020-01-02')
         .add_day({'date': '2020-02-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'})
         .remove_day('2020-02-02')
         .add_day({'date': '2020-03-01', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'})
         .remove_day('2020-03-02')
         .add_day({'date': '2020-04-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'})
         .remove_day('2020-04-02')
         .add_day({'date': '2020-05-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'})
         .remove_day('2020-05-02'),
    )])
    def test_changeset_from_valid_non_empty_dict(self, d: dict, cs: ChangeSet):
        cs0 = ChangeSet(**d)
        assert cs0 == cs

    @pytest.mark.parametrize(['d'], [
        # Invalid day type.
        ({'add': [{'date': '2020-01-01', 'type': 'foo', 'name': 'Holiday'}]},),
        # Invalid date.
        ({'add': [{'date': 'foo', 'type': 'holiday', 'name': 'Holiday'}]},),
        ({'add': [{'date': 'foo', 'type': 'monthly_expiry', 'name': 'Holiday'}]},),
        ({'add': [{'date': 'foo', 'type': 'quarterly_expiry', 'name': 'Holiday'}]},),
        # # Invalid value.
        ({'add': [{'date': '2020-01-01', 'type': 'holiday', 'foo': 'Holiday'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday', 'time': '10:00'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday', 'foo': 'bar'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'monthly_expiry', 'foo': 'Monthly Expiry'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'quarterly_expiry', 'foo': 'Quarterly Expiry'}]},),
        # Invalid day type.
        ({'add': [{'date': '2020-01-01', 'type': 'foo', 'name': 'Special Open', 'time': '10:00'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'foo', 'name': 'Special Close', 'time': '10:00'}]},),
        # Invalid date.
        ({'add': [{'date': 'foo', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'}]},),
        ({'add': [{'date': 'foo', 'type': 'special_close', 'name': 'Special Close', 'time': '10:00'}]},),
        # Invalid value key.
        ({'add': [{'date': '2020-01-01', 'type': 'special_open', 'foo': 'Special Open', 'time': '10:00'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'special_open', 'name': 'Special Open', 'foo': '10:00'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'special_close', 'foo': 'Special Close', 'time': '10:00'}]},),
        ({'add': [{'date': '2020-01-01', 'type': 'special_close', 'name': 'Special Close', 'foo': '10:00'}]},),
        # Invalid date.
        ({'remove': ['2020-01-01', 'foo']},),
    ])
    def test_changeset_from_invalid_dict(self, d: dict):
        with pytest.raises(ValidationError):
            ChangeSet(**d)

    @pytest.mark.parametrize(['d'], [
        # Same day added twice for different day types.
        ({'add': [
            {'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'},
            {'date': '2020-01-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'}
        ]},),
        ({'add': [
            {'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'},
            {'date': '2020-01-01', 'type': 'special_close', 'name': 'Special Close', 'time': '10:00'}
        ]},),
        ({'add': [
            {'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'},
            {'date': '2020-01-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'}
        ]},),
        ({'add': [
            {'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'},
            {'date': '2020-01-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'}
        ]},),
    ])
    def test_changeset_from_inconsistent_dict(self, d: dict):
        with pytest.raises(ValidationError):
            ChangeSet(**d)

    def test_all_days(self):
        cs = ChangeSet(
            add=[
                {'date': '2020-01-01', 'type': 'holiday', 'name': 'Holiday'},
                {'date': '2020-02-01', 'type': 'special_open', 'name': 'Special Open', 'time': '10:00'},
                {'date': '2020-03-01', 'type': 'special_close', 'name': 'Special Close', 'time': '16:00'},
                {'date': '2020-04-01', 'type': 'monthly_expiry', 'name': 'Monthly Expiry'},
                {'date': '2020-05-01', 'type': 'quarterly_expiry', 'name': 'Quarterly Expiry'},
            ],
            remove=['2020-01-02', '2020-02-02', '2020-03-02', '2020-04-02', '2020-05-02']
        )
        assert cs.all_days == tuple(map(lambda x: pd.Timestamp(x), ['2020-01-01', '2020-01-02', '2020-02-01',
                                                                    '2020-02-02', '2020-03-01', '2020-03-02',
                                                                    '2020-04-01', '2020-04-02', '2020-05-01',
                                                                    '2020-05-02']))
