import functools
from datetime import time
from typing import Optional, Callable, ParamSpec, TypeVar, Concatenate, Type

import pandas as pd
from exchange_calendars import calendar_utils, register_calendar_type, ExchangeCalendar, get_calendar_names
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
from exchange_calendars.calendar_utils import _default_calendar_factories

from .changeset import ChangeSet, HolidaysAndSpecialSessions
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
    "ASEX": (ASEXExchangeCalendar, 4),
    #"BMEX": (BMEXExchangeCalendar, 4),
    "XAMS": (XAMSExchangeCalendar, 4),
    "XBRU": (XBRUExchangeCalendar, 4),
    "XBUD": (XBUDExchangeCalendar, 4),
    "XCSE": (XCSEExchangeCalendar, 4),
    "XDUB": (XDUBExchangeCalendar, 4),
    "XETR": (XETRExchangeCalendar, 4),
    #"XHEL": (XHELEXchangeCalendar, 4),
    "XIST": (XISTExchangeCalendar, 4),
    "XJSE": (XJSEExchangeCalendar, 3),
    "XLIS": (XLISExchangeCalendar, 4),
    "XLON": (XLONExchangeCalendar, 4),
    "XMIL": (XMILExchangeCalendar, 4),
    #"XNAS": (XNASExchangeCalendar, 4),
    "XNYS": (XNYSExchangeCalendar, 4),
    "XOSL": (XOSLExchangeCalendar, 4),
    "XPAR": (XPARExchangeCalendar, 4),
    "XPRA": (XPRAExchangeCalendar, 4),
    "XSTO": (XSTOExchangeCalendar, 4),
    "XSWX": (XSWXExchangeCalendar, 4),
    "XTAE": (XTAEExchangeCalendar, 4),
    "XTSE": (XTSEExchangeCalendar, 4),
    "XWAR": (XWARExchangeCalendar, 4),
    "XWBO": (XWBOExchangeCalendar, 4),
}


def apply_extensions() -> None:
    """
    Apply extensions to exchange_calendars.

    This registers all extended calendars in exchange_calendars, overwriting the respective vanilla calendars.
    """
    calendar_names = set(get_calendar_names())

    for k in calendar_names - set(_extensions.keys()):
        cls = _default_calendar_factories.get(k)
        if cls is not None:
            cls = extend_class(cls, day_of_week_expiry=None, changeset_provider=lambda: _changesets.get(k))
            register_calendar_type(k, cls, force=True)

    for k, v in _extensions.items():
        cls, day_of_week_expiry = v
        cls = extend_class(cls, day_of_week_expiry=day_of_week_expiry, changeset_provider=lambda: _changesets.get(k))
        register_calendar_type(k, cls, force=True)


def register_extension(name: str, cls: Type[ExchangeCalendar], day_of_week_expiry: Optional[int] = None) -> None:
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
    _extensions[name] = (cls, day_of_week_expiry)


def _remove_calendar_from_factory_cache(name: str):
    """
    Remove a cached calendar instance for the given exchange key from the factory cache.

    Caveat: This function accesses the private attribute _factory_output_cache of the global calendar dispatcher.
    """
    # noinspection PyProtectedMember
    calendar_utils.global_calendar_dispatcher._factory_output_cache.pop(name, None)


P = ParamSpec('P')
R = TypeVar('R')


def _with_changeset(f: Callable[Concatenate[ChangeSet, P], R]) -> Callable[Concatenate[str, P], R]:
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
        cs: ChangeSet = _changesets.get(exchange, ChangeSet())

        # Call wrapped function with changeset as first positional argument.
        result = f(cs, *args, **kwargs)

        if not cs.is_consistent():
            raise ValueError(f'Changeset for {str} is inconsistent: {cs}.')

        # Save changeset back to _changesets.
        _changesets[exchange] = cs

        # Remove calendar for exchange key from factory cache.
        _remove_calendar_from_factory_cache(exchange)

        # Return result of wrapped function.
        return result

    return wrapper


@_with_changeset
def _add_day(cs: ChangeSet, day_type: HolidaysAndSpecialSessions, date: pd.Timestamp, *args) -> None:
    """
    Add a day of a given type to the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset to which to add the day.
    day_type : HolidaysAndSpecialSessions
        The type of the day to add.
    date : pd.Timestamp
        The date to add.
    *args : Any
        The properties to add for the day. Must match the properties required by the given day type.

    Returns
    -------
    None
    """
    cs.changes[day_type].add_day(date, args)


def add_day(exchange: str, day_type: HolidaysAndSpecialSessions, date: pd.Timestamp, *args) -> None:
    _add_day(exchange, day_type, date, *args)


@_with_changeset
def _remove_day(cs: ChangeSet, day_type: HolidaysAndSpecialSessions, date: pd.Timestamp) -> None:
    """
    Remove a day of a given type from the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset from which to remove the day.
    day_type : HolidaysAndSpecialSessions
        The type of the day to remove.
    date : pd.Timestamp
        The date to remove.

    Returns
    -------
    None
    """
    cs.changes[day_type].remove_day(date)


def remove_day(exchange: str, day_type: Optional[HolidaysAndSpecialSessions], date: pd.Timestamp) -> None:
    if day_type is not None:
        _remove_day(exchange, day_type, date)
    else:
        for day_type0 in HolidaysAndSpecialSessions:
            _remove_day(exchange, day_type0, date)


def add_holiday(exchange: str, date: pd.Timestamp, name: str = "Holiday") -> None:
    """
    Add a holiday to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : pd.Timestamp
        The date of the holiday.
    name : str
        The name of the holiday.

    Returns
    -------
    None
    """
    _add_day(exchange, HolidaysAndSpecialSessions.HOLIDAY, date, name)


def remove_holiday(exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a holiday from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : pd.Timestamp
        The date of the holiday to remove.

    Returns
    -------
    None
    """
    _remove_day(exchange, HolidaysAndSpecialSessions.HOLIDAY, date)


def add_special_open(exchange: str, date: pd.Timestamp, t: time, name: str = "Special Open") -> None:
    """
    Add a special open to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
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
    _add_day(exchange, HolidaysAndSpecialSessions.SPECIAL_OPEN, date, t, name)


def remove_special_open(exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a special close from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : pd.Timestamp
        The date of the special open to remove.

    Returns
    -------
    None
    """
    _remove_day(exchange, HolidaysAndSpecialSessions.SPECIAL_OPEN, date)


def add_special_close(exchange: str, date: pd.Timestamp, t: time, name: str = "Special Close") -> None:
    """
    Add a special close to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
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
    _add_day(exchange, HolidaysAndSpecialSessions.SPECIAL_CLOSE, date, t, name)


def remove_special_close(exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a special close from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : pd.Timestamp
        The date of the special close to remove.

    Returns
    -------
    None
    """
    _remove_day(exchange, HolidaysAndSpecialSessions.SPECIAL_CLOSE, date)


def add_quarterly_expiry(exchange: str, date: pd.Timestamp, name: str = "Quarterly Expiry") -> None:
    """
    Add a quarterly expiry to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : pd.Timestamp
        The date of the quarterly expiry.
    name : str
        The name of the quarterly expiry.

    Returns
    -------
    None
    """
    _add_day(exchange, HolidaysAndSpecialSessions.QUARTERLY_EXPIRY, date, name)


def remove_quarterly_expiry(exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a quarterly expiry from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : pd.Timestamp
        The date of the quarterly expiry to remove.

    Returns
    -------
    None
    """
    _remove_day(exchange, HolidaysAndSpecialSessions.QUARTERLY_EXPIRY, date)


def add_monthly_expiry(exchange: str, date: pd.Timestamp, name: str = "Monthly Expiry") -> None:
    """
    Add a monthly expiry to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : pd.Timestamp
        The date of the monthly expiry.
    name : str
        The name of the monthly expiry.

    Returns
    -------
    None
    """
    _add_day(exchange, HolidaysAndSpecialSessions.MONTHLY_EXPIRY, date, name)

    
def remove_monthly_expiry(exchange: str, date: pd.Timestamp) -> None:
    """
    Remove a monthly expiry from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : pd.Timestamp
        The date of the monthly expiry to remove.

    Returns
    -------
    None
    """
    _remove_day(exchange, HolidaysAndSpecialSessions.MONTHLY_EXPIRY, date)

    
@_with_changeset
def reset_calendar(cs: ChangeSet) -> None:
    """
    Reset an exchange calendar to its original state.

    Parameters
    ----------
    cs : ChangeSet
        The changeset to reset.

    Returns
    -------
    None
    """
    cs.clear()
    

# Declare public names.
__all__ = ["apply_extensions", "register_extension", "extend_class", "HolidaysAndSpecialSessions", "add_day",
           "remove_day", "add_holiday", "remove_holiday", "add_special_close", "remove_special_close",
           "add_special_open", "remove_special_open", "add_quarterly_expiry", "remove_quarterly_expiry",
           "add_monthly_expiry", "remove_monthly_expiry", "ExtendedExchangeCalendar"]

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
