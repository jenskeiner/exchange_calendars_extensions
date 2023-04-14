import datetime
from types import NoneType
from typing import Union

import exchange_calendars as ec
import pandas as pd
from exchange_calendars import register_calendar_type
from exchange_calendars.exchange_calendar_asex import ASEXExchangeCalendar
from exchange_calendars.exchange_calendar_xams import XAMSExchangeCalendar
from exchange_calendars.exchange_calendar_xbru import XBRUExchangeCalendar
from exchange_calendars.exchange_calendar_xbud import XBUDExchangeCalendar
from exchange_calendars.exchange_calendar_xcse import XCSEExchangeCalendar
from exchange_calendars.exchange_calendar_xdub import XDUBExchangeCalendar
from exchange_calendars.exchange_calendar_xetr import XETRExchangeCalendar
from exchange_calendars.exchange_calendar_xist import XISTExchangeCalendar
from exchange_calendars.exchange_calendar_xjse import XJSEExchangeCalendar
from exchange_calendars.exchange_calendar_xlis import XLISExchangeCalendar
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars.exchange_calendar_xmil import XMILExchangeCalendar
from exchange_calendars.exchange_calendar_xnys import XNYSExchangeCalendar
from exchange_calendars.exchange_calendar_xosl import XOSLExchangeCalendar
from exchange_calendars.exchange_calendar_xpar import XPARExchangeCalendar
from exchange_calendars.exchange_calendar_xpra import XPRAExchangeCalendar
from exchange_calendars.exchange_calendar_xsto import XSTOExchangeCalendar
from exchange_calendars.exchange_calendar_xswx import XSWXExchangeCalendar
from exchange_calendars.exchange_calendar_xtae import XTAEExchangeCalendar
from exchange_calendars.exchange_calendar_xtse import XTSEExchangeCalendar
from exchange_calendars.exchange_calendar_xwar import XWARExchangeCalendar
from exchange_calendars.exchange_calendar_xwbo import XWBOExchangeCalendar

from .changeset import ExchangeCalendarChangeSet
from .holiday_calendar import extend_class, ExtendedExchangeCalendar

# TODO: Add the following exchanges:
# class BMEXExchangeCalendar:
#     pass
#
#
# class XHELEXchangeCalendar:
#     pass
#
#
# class XNASExchangeCalendar:
#     pass


_changesets = dict()

_extensions = {
    "ASEX": extend_class(ASEXExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("ASEX")),
    #"BMEX": extend_class(BMEXExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("BMEX")),
    "XAMS": extend_class(XAMSExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XAMS")),
    "XBRU": extend_class(XBRUExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XBRU")),
    "XBUD": extend_class(XBUDExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XBUD")),
    "XCSE": extend_class(XCSEExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XCSE")),
    "XDUB": extend_class(XDUBExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XDUB")),
    "XETR": extend_class(XETRExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XETR")),
    #"XHEL": extend_class(XHELEXchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XHEL")),
    "XIST": extend_class(XISTExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XIST")),
    "XJSE": extend_class(XJSEExchangeCalendar, day_of_week_expiry=3, changeset_provider=lambda: _changesets.get("XJSE")),
    "XLIS": extend_class(XLISExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XLIS")),
    "XLON": extend_class(XLONExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XLON")),
    "XMIL": extend_class(XMILExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XMIL")),
    #"XNAS": extend_class(XNASExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XNAS")),
    "XNYS": extend_class(XNYSExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XNYS")),
    "XOSL": extend_class(XOSLExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XOSL")),
    "XPAR": extend_class(XPARExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XPAR")),
    "XPRA": extend_class(XPRAExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XPRA")),
    "XSTO": extend_class(XSTOExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XSTO")),
    "XSWX": extend_class(XSWXExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XSWX")),
    "XTAE": extend_class(XTAEExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XTAE")),
    "XTSE": extend_class(XTSEExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XTSE")),
    "XWAR": extend_class(XWARExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XWAR")),
    "XWBO": extend_class(XWBOExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XWBO")),
}


def apply_extensions():
    """Apply extensions to exchange_calendars."""
    for k, v in _extensions.items():
        register_calendar_type(k, v, force=True)


def register_extension(name, cls, day_of_week_expiry: Union[NoneType, int] = None):
    """Set an extension for a given exchange calendar."""
    _extensions[name] = extend_class(cls, day_of_week_expiry=day_of_week_expiry, changeset_provider=lambda: _changesets.get(name))


def _remove_calendar_from_factory_cache(name: str):
    """Remove a calendar from the factory cache."""
    # noinspection PyProtectedMember
    ec.calendar_utils.global_calendar_dispatcher._factory_output_cache.pop(name, None)


# Define an annotation that uses the keyword parameter 'exchange', passed to the decorated function, to obtain the
# corresponding changeset via _changesets. The retrieved changeset is then passed to the decorated function in the
# keyword argument 'cs'. Also, after the decorated function has finished, the changeset is updated in the _changesets
# dictionary. Also, the calendar is removed from the factory cache.
def _calendar_modification(f):
    def wrapper(exchange: str, *args, **kwargs):
        cs = _changesets.get(exchange, ExchangeCalendarChangeSet())
        result = f(cs, *args, **kwargs)
        _changesets[exchange] = cs
        _remove_calendar_from_factory_cache(exchange)
        return result
    return wrapper


@_calendar_modification
def add_holiday(cs: ExchangeCalendarChangeSet, date: pd.Timestamp, name: str = "Holiday"):
    """Add a holiday to an exchange calendar."""
    # Check if holiday to add is already in the set of holidays to remove.
    if date in cs.holidays_remove:
        # Remove the holiday from the set of holidays to remove.
        cs.holidays_remove.remove(date)
    # Add the holiday to the set of holidays to add.
    cs.holidays_add.add((date, name))


@_calendar_modification
def remove_holiday(cs: ExchangeCalendarChangeSet, date: pd.Timestamp):
    """Remove a holiday from an exchange calendar."""
    # Check if holiday to remove is already in the set of holidays to add.
    if date in map(lambda x: x[0], cs.holidays_add):
        # Find the tuple that corresponds to the holiday to remove.
        elem = next(x for x in cs.holidays_add if x[0] == date)

        # Remove element from the set.
        cs.holidays_add.remove(elem)

    # Add the holiday to the set of holidays to remove.
    cs.holidays_remove.add(date)


@_calendar_modification
def add_special_close(cs: ExchangeCalendarChangeSet, date: pd.Timestamp, t: datetime.time, name: str = "Special Close"):
    """Add a special close to an exchange calendar."""
    # Check if special close to add is already in the set of special closes to remove.
    if date in cs.special_closes_remove:
        # Remove the special close from the set of special closes to remove.
        cs.special_closes_remove.remove(date)

    # Add the special close to the set of special closes to add.
    cs.special_closes_add.add((date, t, name))


@_calendar_modification
def remove_special_close(cs: ExchangeCalendarChangeSet, date: pd.Timestamp):
    """Remove a special close from an exchange calendar."""
    # Check if special close to remove is already in the set of special closes to add.
    if date in map(lambda x: x[0], cs.special_closes_add):
        # Find the tuple that corresponds to the special close to remove.
        elem = next(x for x in cs.special_closes_add if x[0] == date)

        # Remove element from the set.
        cs.special_closes_add.remove(elem)

    # Add the special close to the set of special closes to remove.
    cs.special_closes_remove.add(date)


@_calendar_modification
def add_special_open(cs: ExchangeCalendarChangeSet, date: pd.Timestamp, t: datetime.time, name: str = "Special Open"):
    """Add a special open to an exchange calendar."""
    # Check if special open to add is already in the set of special opens to remove.
    if date in cs.special_opens_remove:
        # Remove the special open from the set of special opens to remove.
        cs.special_opens_remove.remove(date)
    # Add the special open to the set of special opens to add.
    cs.special_opens_add.add((date, t, name))


@_calendar_modification
def remove_special_open(cs: ExchangeCalendarChangeSet, date: pd.Timestamp):
    """Remove a special close from an exchange calendar."""
    # Check if special open to remove is already in the set of special opens to add.
    if date in map(lambda x: x[0], cs.special_opens_add):
        # Find the tuple that corresponds to the special open to remove.
        elem = next(x for x in cs.special_opens_add if x[0] == date)

        # Remove element from the set.
        cs.special_opens_add.remove(elem)

    # Add the special open to the set of special opens to remove.
    cs.special_opens_remove.add(date)


@_calendar_modification
def add_quarterly_expiry(cs: ExchangeCalendarChangeSet, date: pd.Timestamp, name: str = "Quarterly Expiry"):
    """Add a quarterly expiry to an exchange calendar."""
    # Check if quarterly expiry to add is already in the set of quarterly expiries to remove.
    if date in cs.quarterly_expiries_remove:
        # Remove the quarterly expiry from the set of quarterly expiries to remove.
        cs.quarterly_expiries_remove.remove(date)
    # Add the quarterly expiry to the set of quarterly expiries to add.
    cs.quarterly_expiries_add.add((date, name))


@_calendar_modification
def remove_quarterly_expiry(cs: ExchangeCalendarChangeSet, date: pd.Timestamp):
    """Remove a quarterly expiry from an exchange calendar."""
    # Check if quarterly expiry to remove is already in the set of quarterly expiries to add.
    if date in map(lambda x: x[0], cs.quarterly_expiries_add):
        # Find the tuple that corresponds to the quarterly expiry to remove.
        elem = next(x for x in cs.quarterly_expiries_add if x[0] == date)

        # Remove element from the set.
        cs.quarterly_expiries_add.remove(elem)

    # Add the quarterly expiry to the set of quarterly expiries to remove.
    cs.quarterly_expiries_remove.add(date)


@_calendar_modification
def add_monthly_expiry(cs: ExchangeCalendarChangeSet, date: pd.Timestamp, name: str = "Monthly Expiry"):
    """Add a monthly expiry to an exchange calendar."""
    # Check if monthly expiry to add is already in the set of monthly expiries to remove.
    if date in cs.monthly_expiries_remove:
        # Remove the monthly expiry from the set of monthly expiries to remove.
        cs.monthly_expiries_remove.remove(date)
    # Add the monthly expiry to the set of monthly expiries to add.
    cs.monthly_expiries_add.add((date, name))
    
    
@_calendar_modification
def remove_monthly_expiry(cs: ExchangeCalendarChangeSet, date: pd.Timestamp):
    """Remove a monthly expiry from an exchange calendar."""
    # Check if monthly expiry to remove is already in the set of monthly expiries to add.
    if date in map(lambda x: x[0], cs.monthly_expiries_add):
        # Find the tuple that corresponds to the monthly expiry to remove.
        elem = next(x for x in cs.monthly_expiries_add if x[0] == date)

        # Remove element from the set.
        cs.monthly_expiries_add.remove(elem)

    # Add the monthly expiry to the set of monthly expiries to remove.
    cs.monthly_expiries_remove.add(date)
    
    
@_calendar_modification
def reset_calendar(cs: ExchangeCalendarChangeSet):
    cs.clear()
    
        
    
__all__ = ["apply_extensions", "register_extension", "extend_class", "add_holiday", "remove_holiday",
           "add_special_close", "remove_special_close", "add_special_open", "remove_special_open",
           "ExtendedExchangeCalendar"]

__version__ = None

try:
    from importlib.metadata import version
    # get version from installed package
    __version__ = version("exchange_calendars_extensions")
except ImportError:
    pass

if __version__ is None:
    try:
        # if package not installed, get version as set when package built
        from ._version import version
    except Exception:
        # If package not installed and not built, leave __version__ as None
        pass
    else:
        __version__ = version

del version
