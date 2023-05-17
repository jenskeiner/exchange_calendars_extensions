import functools
from datetime import time
from types import NoneType
from typing import Union, Optional, Callable, ParamSpec, TypeVar, Concatenate

import pandas as pd
from exchange_calendars import calendar_utils, register_calendar_type
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

from .changeset import ExchangeCalendarChangeSet, HolidaysAndSpecialSessions
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

# Dictionary that maps from exchange key to ExchangeCalendarChangeSet. Contains all changesets to apply when creating a
# new calendar instance.
_changesets = dict()

# Dictionary that maps from exchange key to ExtendedExchangeCalendar. Contains all extended calendars classes that
# replace the vanilla classes in exchange_calendars when calling apply_extensions().
#
# Note: The values in this dictionary use extend_class() to create the extended classes, respectively for each exchange,
#     based on the respective vanilla class in exchange_calendars. Also, the changeset_provider is set to a lambda
#     function that returns the changeset for the respective exchange in _changesets, or None, if no changeset exists.
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


def apply_extensions() -> None:
    """
    Apply extensions to exchange_calendars.

    This registers all extended calendars in exchange_calendars, overwriting the respective vanilla calendars.
    """
    for k, v in _extensions.items():
        register_calendar_type(k, v, force=True)


def register_extension(name: str, cls: type, day_of_week_expiry: Optional[int] = None) -> None:
    """
    Register an extended calendar class for a given exchange key and a given base class.

    This creates and then registers an extended calendar class based on the given class, with support for all
    additional properties of ExtendedExchangeCalendar. Expiry days are on the third instance of the given day of the
    week in each month. The extended class also supports programmatic modifications; see e.g. add_holiday().

    Parameters
    ----------
    name : str
        The exchange key for which to register the extended calendar class.
    cls : type
        The base class to extend.
    day_of_week_expiry : Optional[int]
        The day of the week on which options expire. If None, expiry days are not supported.

    Returns
    -------
    None
    """
    _extensions[name] = extend_class(cls, day_of_week_expiry=day_of_week_expiry,
                                     changeset_provider=lambda: _changesets.get(name))


def _remove_calendar_from_factory_cache(name: str):
    """
    Remove a cached calendar instance for the given exchange key from the factory cache.

    Caveat: This function accesses the private attribute _factory_output_cache of the global calendar dispatcher.
    """
    # noinspection PyProtectedMember
    calendar_utils.global_calendar_dispatcher._factory_output_cache.pop(name, None)


P = ParamSpec('P')
R = TypeVar('R')


def _calendar_modification(f: Callable[Concatenate[ExchangeCalendarChangeSet, str, P], R]) -> Callable[Concatenate[str, P], R]:
    """
    An annotation that obtains the changeset from _changesets that corresponds to the exchange key passed as the first
    positional argument to the wrapped function. Instead of passing the key, passes the retrieved changeset, or a newly
    created empty one, if no entry for the key exists yet, to the wrapped function.

    After the wrapped function has finished, saves the changeset back to _changesets under the key. Note that this only
    has an effect if the changeset was newly created upon retrieval, before the wrapped call. Otherwise, the changeset
    will already be in _changesets.

    Finally, removes the calendar for the exchange key from the factory cache. This ensures that the next call to
    get_calendar() for the exchange key will create a new calendar instance, which will reflect the changes made by the
    wrapped function.

    Parameters
    ----------
    f : Callable
        The function to wrap.

    Returns
    -------
    Callable
        The wrapped function.
    """
    @functools.wraps(f)
    def wrapper(exchange: str, *args: P.args, **kwargs: P.kwargs) -> R:
        # Retrieve changeset for key, create new empty one, if required.
        cs: ExchangeCalendarChangeSet = _changesets.get(exchange, ExchangeCalendarChangeSet())

        # Call wrapped function with changeset as first positional argument.
        result = f(cs, exchange, *args, **kwargs)

        # Save changeset back to _changesets.
        _changesets[exchange] = cs

        # Remove calendar for exchange key from factory cache.
        _remove_calendar_from_factory_cache(exchange)

        # Return result of wrapped function.
        return result

    return wrapper


@_calendar_modification
def add_holiday(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp, name: str = "Holiday") -> None:
    """
    Add a holiday to an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset to which to add the holiday.
    date : pd.Timestamp
        The date of the holiday.
    name : str
        The name of the holiday.

    Returns
    -------
    None
    """
    cs.changes[HolidaysAndSpecialSessions.HOLIDAY].add_day(date, name)


@_calendar_modification
def remove_holiday(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a holiday from an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset from which to remove the holiday.
    date : pd.Timestamp
        The date of the holiday to remove.

    Returns
    -------
    None
    """
    cs.changes[HolidaysAndSpecialSessions.HOLIDAY].remove_day(date)


@_calendar_modification
def add_special_open(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp, t: time, name: str = "Special Open") -> None:
    """
    Add a special open to an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset to which to add the special open.
    date : pd.Timestamp
        The date of the special open.
    t : time
        The time of the special open.
    name : str
        The name of the special open.

    Returns
    -------
    None
    """
    # Check if special open to add is already in the set of special opens to remove.
    if date in cs.special_opens_remove:
        # Remove the special open from the set of special opens to remove.
        cs.special_opens_remove.remove(date)
    # Add the special open to the set of special opens to add.
    cs.special_opens_add.add((date, t, name))


@_calendar_modification
def remove_special_open(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a special close from an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset from which to remove the special open.
    date : pd.Timestamp
        The date of the special open to remove.

    Returns
    -------
    None
    """
    # Check if special open to remove is already in the set of special opens to add.
    if date in map(lambda x: x[0], cs.special_opens_add):
        # Find the tuple that corresponds to the special open to remove.
        elem = next(x for x in cs.special_opens_add if x[0] == date)

        # Remove element from the set.
        cs.special_opens_add.remove(elem)

    # Add the special open to the set of special opens to remove.
    cs.special_opens_remove.add(date)


@_calendar_modification
def add_special_close(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp, t: time, name: str = "Special Close") -> None:
    """
    Add a special close to an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset to which to add the special close.
    date : pd.Timestamp
        The date of the special close.
    t : time
        The time of the special close.
    name : str
        The name of the special close.

    Returns
    -------
    None
    """
    # Check if special close to add is already in the set of special closes to remove.
    if date in cs.special_closes_remove:
        # Remove the special close from the set of special closes to remove.
        cs.special_closes_remove.remove(date)

    # Add the special close to the set of special closes to add.
    cs.special_closes_add.add((date, t, name))


@_calendar_modification
def remove_special_close(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a special close from an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset from which to remove the special close.
    date : pd.Timestamp
        The date of the special close to remove.

    Returns
    -------
    None
    """
    # Check if special close to remove is already in the set of special closes to add.
    if date in map(lambda x: x[0], cs.special_closes_add):
        # Find the tuple that corresponds to the special close to remove.
        elem = next(x for x in cs.special_closes_add if x[0] == date)

        # Remove element from the set.
        cs.special_closes_add.remove(elem)

    # Add the special close to the set of special closes to remove.
    cs.special_closes_remove.add(date)


@_calendar_modification
def add_quarterly_expiry(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp, name: str = "Quarterly Expiry") -> None:
    """
    Add a quarterly expiry to an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset to which to add the quarterly expiry.
    date : pd.Timestamp
        The date of the quarterly expiry.
    name : str
        The name of the quarterly expiry.

    Returns
    -------
    None
    """
    # Check if quarterly expiry to add is already in the set of quarterly expiries to remove.
    if date in cs.quarterly_expiries_remove:
        # Remove the quarterly expiry from the set of quarterly expiries to remove.
        cs.quarterly_expiries_remove.remove(date)
    # Add the quarterly expiry to the set of quarterly expiries to add.
    cs.quarterly_expiries_add.add((date, name))


@_calendar_modification
def remove_quarterly_expiry(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a quarterly expiry from an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset from which to remove the quarterly expiry.
    date : pd.Timestamp
        The date of the quarterly expiry to remove.

    Returns
    -------
    None
    """
    # Check if quarterly expiry to remove is already in the set of quarterly expiries to add.
    if date in map(lambda x: x[0], cs.quarterly_expiries_add):
        # Find the tuple that corresponds to the quarterly expiry to remove.
        elem = next(x for x in cs.quarterly_expiries_add if x[0] == date)

        # Remove element from the set.
        cs.quarterly_expiries_add.remove(elem)

    # Add the quarterly expiry to the set of quarterly expiries to remove.
    cs.quarterly_expiries_remove.add(date)


@_calendar_modification
def add_monthly_expiry(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp, name: str = "Monthly Expiry") -> None:
    """
    Add a monthly expiry to an exchange calendar.

    Parameters
    ----------
    exchange : ExchangeCalendarChangeSet
        The changeset to which to add the monthly expiry.
    date : pd.Timestamp
        The date of the monthly expiry.
    name : str
        The name of the monthly expiry.

    Returns
    -------
    None
    """
    # Check if monthly expiry to add is already in the set of monthly expiries to remove.
    if date in cs.monthly_expiries_remove:
        # Remove the monthly expiry from the set of monthly expiries to remove.
        cs.monthly_expiries_remove.remove(date)
    # Add the monthly expiry to the set of monthly expiries to add.
    cs.monthly_expiries_add.add((date, name))
    
    
@_calendar_modification
def remove_monthly_expiry(cs: ExchangeCalendarChangeSet, exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a monthly expiry from an exchange calendar.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset from which to remove the monthly expiry.
    date : pd.Timestamp
        The date of the monthly expiry to remove.

    Returns
    -------
    None
    """
    # Check if monthly expiry to remove is already in the set of monthly expiries to add.
    if date in map(lambda x: x[0], cs.monthly_expiries_add):
        # Find the tuple that corresponds to the monthly expiry to remove.
        elem = next(x for x in cs.monthly_expiries_add if x[0] == date)

        # Remove element from the set.
        cs.monthly_expiries_add.remove(elem)

    # Add the monthly expiry to the set of monthly expiries to remove.
    cs.monthly_expiries_remove.add(date)
    
    
@_calendar_modification
def reset_calendar(cs: ExchangeCalendarChangeSet) -> None:
    """
    Reset an exchange calendar to its original state.

    Parameters
    ----------
    cs : ExchangeCalendarChangeSet
        The changeset to reset.

    Returns
    -------
    None
    """
    cs.clear()
    

# Declare public names.
__all__ = ["apply_extensions", "register_extension", "extend_class", "add_holiday", "remove_holiday",
           "add_special_close", "remove_special_close", "add_special_open", "remove_special_open",
           "add_quarterly_expiry", "remove_quarterly_expiry", "add_monthly_expiry", "remove_monthly_expiry",
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
