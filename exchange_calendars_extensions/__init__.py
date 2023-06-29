import functools
from datetime import time
from typing import Optional, Callable, Type, Union, Any

from exchange_calendars import calendar_utils, register_calendar_type, ExchangeCalendar, get_calendar_names
from exchange_calendars.calendar_utils import _default_calendar_factories
from exchange_calendars.exchange_calendar_asex import ASEXExchangeCalendar
from exchange_calendars.exchange_calendar_xams import XAMSExchangeCalendar
from exchange_calendars.exchange_calendar_xbru import XBRUExchangeCalendar
from exchange_calendars.exchange_calendar_xbud import XBUDExchangeCalendar
from exchange_calendars.exchange_calendar_xcse import XCSEExchangeCalendar
from exchange_calendars.exchange_calendar_xdub import XDUBExchangeCalendar
from exchange_calendars.exchange_calendar_xetr import XETRExchangeCalendar
from exchange_calendars.exchange_calendar_xhel import XHELExchangeCalendar
from exchange_calendars.exchange_calendar_xist import XISTExchangeCalendar
from exchange_calendars.exchange_calendar_xjse import XJSEExchangeCalendar
from exchange_calendars.exchange_calendar_xlis import XLISExchangeCalendar
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars.exchange_calendar_xmad import XMADExchangeCalendar
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
from typing_extensions import ParamSpec, Concatenate

from .changeset import ChangeSet, DayType, DaySpec, DayWithTimeSpec
from .holiday_calendar import extend_class, ExtendedExchangeCalendar, ExchangeCalendarExtensions

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
    "XAMS": (XAMSExchangeCalendar, 4),
    "XBRU": (XBRUExchangeCalendar, 4),
    "XBUD": (XBUDExchangeCalendar, 4),
    "XCSE": (XCSEExchangeCalendar, 4),
    "XDUB": (XDUBExchangeCalendar, 4),
    "XETR": (XETRExchangeCalendar, 4),
    "XHEL": (XHELExchangeCalendar, 4),
    "XIST": (XISTExchangeCalendar, 4),
    "XJSE": (XJSEExchangeCalendar, 3),
    "XLIS": (XLISExchangeCalendar, 4),
    "XLON": (XLONExchangeCalendar, 4),
    "XMAD": (XMADExchangeCalendar, 4),
    "XMIL": (XMILExchangeCalendar, 4),
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


_original_classes = dict()


def apply_extensions() -> None:
    """
    Apply extensions to exchange_calendars.

    This registers all extended calendars in exchange_calendars, overwriting the respective vanilla calendars.
    """
    if len(_original_classes) > 0:
        # Extensions have already been applied.
        return

    calendar_names = set(get_calendar_names())

    def get_changeset_fn(name: str) -> Callable[[], ChangeSet]:
        def fn() -> ChangeSet:
            return _changesets.get(name)
        return fn

    for k in calendar_names - set(_extensions.keys()):
        cls = _default_calendar_factories.get(k)
        if cls is not None:
            # Store the original class for later use.
            _original_classes[k] = cls
            # Create extended class.
            cls = extend_class(cls, day_of_week_expiry=None, changeset_provider=get_changeset_fn(k))
            # Register extended class.
            register_calendar_type(k, cls, force=True)
            # Remove original class from factory cache.
            _remove_calendar_from_factory_cache(k)

    for k, v in _extensions.items():
        cls, day_of_week_expiry = v
        # Store the original class for later use.
        _original_classes[k] = cls
        # Create extended class.
        cls = extend_class(cls, day_of_week_expiry=day_of_week_expiry, changeset_provider=get_changeset_fn(k))
        # Register extended class.
        register_calendar_type(k, cls, force=True)
        # Remove original class from factory cache.
        _remove_calendar_from_factory_cache(k)


def remove_extensions() -> None:
    """
    Remove extensions from exchange_calendars.

    This removes all extended calendars from exchange_calendars, restoring the respective vanilla calendars.
    """
    if len(_original_classes) == 0:
        # Extensions have not been applied.
        return

    for k, v in _original_classes.items():
        # Register original class.
        register_calendar_type(k, v, force=True)
        # Remove extended class from factory cache.
        _remove_calendar_from_factory_cache(k)

    _original_classes.clear()


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


def _with_changeset(f: Callable[Concatenate[ChangeSet, P], ChangeSet]) -> Callable[Concatenate[str, P], None]:
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
    def wrapper(exchange: str, *args: P.args, **kwargs: P.kwargs) -> None:
        # Retrieve changeset for key, create new empty one, if required.
        cs: ChangeSet = _changesets.get(exchange, ChangeSet())

        # Call wrapped function with changeset as first positional argument.
        cs = f(cs, *args, **kwargs)

#        if not cs.is_consistent():
#            raise ValueError(f'Changeset for {str} is inconsistent: {cs}.')

        # Save changeset back to _changesets.
        _changesets[exchange] = cs

        # Remove calendar for exchange key from factory cache.
        _remove_calendar_from_factory_cache(exchange)

        # Return result of wrapped function.
        return None

    return wrapper


@_with_changeset
def _add_day(cs: ChangeSet, date: Any, value: Union[DaySpec, DayWithTimeSpec, dict], day_type: DayType, strict: bool) -> ChangeSet:
    """
    Add a day of a given type to the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset to which to add the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    value : Union[DaySpec, DaySpecWithTime, dict]
        The properties to add for the day. Must match the properties required by the given day type.
    day_type : DayType
        The type of the day to add.
    strict : bool
        Whether to raise an error if the changeset would be inconsistent after adding the day.

    Returns
    -------
    ChangeSet
        The changeset with the added day.

    Raises
    ------
    ValueError
        If the changeset would be inconsistent after adding the day.
    """
    if not strict:
        cs.clear_day(date)

    return cs.add_day(date, value, day_type)


def add_day(exchange: str, date: Any, value: Union[DaySpec, DayWithTimeSpec], day_type: DayType, strict: bool = False) -> None:
    """
    Add a day of a given type to the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    value : Union[DaySpec, DaySpecWithTime]
        The properties to add for the day. Must match the properties required by the given day type.
    day_type : DayType
        The type of the day to add.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after adding the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, value, day_type, strict=strict)


@_with_changeset
def _remove_day(cs: ChangeSet, date: Any, day_type: DayType, strict: bool) -> ChangeSet:
    """
    Remove a day of a given type from the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset from which to remove the day.
    date : Any
        The date to remove. Must be convertible to pandas.Timestamp.
    day_type : DayType
        The type of the day to remove.
    strict : bool
        Whether to raise an error if the changeset would be inconsistent after removing the day.

    Returns
    -------
    ChangeSet
        The changeset with the removed day.

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after removing the day.
    """
    if not strict:
        cs.clear_day(date)

    return cs.remove_day(date, day_type)


def remove_day(exchange: str, date: Any, day_type: Optional[DayType] = None, strict: bool = False) -> None:
    """
    Remove a day of a given type from the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : Any
        The date to remove. Must be convertible to pandas.Timestamp.
    day_type : Optional[DayType]
        The type of the day to remove. If None, removes the day for all types of days.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after removing the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after removing the day.
    """
    _remove_day(exchange, date, day_type, strict=strict)


@_with_changeset
def _reset_day(cs: ChangeSet, date: Any, day_type: Optional[DayType] = None) -> ChangeSet:
    """
    Clear a day of a given type from the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset from which to clear the day.
    date : Any
        The date to clear. Must be convertible to pandas.Timestamp.
    day_type : Optional[DayType]
        The type of the day to clear. If None, clears all types of days.

    Returns
    -------
    ChangeSet
        The changeset with the cleared day.
    """
    return cs.clear_day(date, day_type)


def reset_day(exchange: str, date: Any, day_type: Optional[DayType] = None) -> None:
    """
    Clear a day of a given type from the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to clear the day.
    date : Any
        The date to clear. Must be convertible to pandas.Timestamp.
    day_type : Optional[DayType]
        The type of the day to clear. If None, clears all types of days.

    Returns
    -------
    None
    """
    _reset_day(exchange, date, day_type)


def add_holiday(exchange: str, date: Any, name: str = "Holiday", strict: bool = False) -> None:
    """
    Add a holiday to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    name : str
        The name of the holiday.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after adding the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"name": name}, DayType.HOLIDAY, strict=strict)


def remove_holiday(exchange: str, date: Any, strict: bool = False) -> None:
    """
    Remove a holiday from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : Any
        The date to remove. Must be convertible to pandas.Timestamp.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after removing the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after removing the day.
    """
    _remove_day(exchange, date, DayType.HOLIDAY, strict=strict)


def reset_holiday(exchange: str, date: Any) -> None:
    """
    Clear a holiday from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to clear the day.
    date : Any
        The date to clear. Must be convertible to pandas.Timestamp.

    Returns
    -------
    None
    """
    _reset_day(exchange, date, DayType.HOLIDAY)


def add_special_open(exchange: str, date: Any, t: Union[time, str], name: str = "Special Open", strict: bool = False) -> None:
    """
    Add a special open to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    t : Union[time, str]
        The time of the special open. If a string, must be in the format 'HH:MM' or 'HH:MM:SS'.
    name : str
        The name of the special open.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after adding the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"name": name, "time": t}, DayType.SPECIAL_OPEN, strict=strict)


def remove_special_open(exchange: str, date: Any, strict: bool = False) -> None:
    """
    Remove a special close from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : Any
        The date to remove. Must be convertible to pandas.Timestamp.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after removing the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after removing the day.
    """
    _remove_day(exchange, date, DayType.SPECIAL_OPEN, strict=strict)


def reset_special_open(exchange: str, date: Any) -> None:
    """
    Clear a special open from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to clear the day.
    date : Any
        The date to clear. Must be convertible to pandas.Timestamp.

    Returns
    -------
    None
    """
    _reset_day(exchange, date, DayType.SPECIAL_OPEN)


def add_special_close(exchange: str, date: Any, t: Union[time, str], name: str = "Special Close", strict: bool = False) -> None:
    """
    Add a special close to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    t : Union[time, str]
        The time of the special close. If a string, must be in the format 'HH:MM' or 'HH:MM:SS'.
    name : str
        The name of the special close.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after adding the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"name": name, "time": t}, DayType.SPECIAL_CLOSE, strict=strict)


def remove_special_close(exchange: str, date: Any, strict: bool = False) -> None:
    """
    Remove a special close from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : Any
        The date to remove. Must be convertible to pandas.Timestamp.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after removing the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after removing the day.
    """
    _remove_day(exchange, date, DayType.SPECIAL_CLOSE, strict=strict)


def reset_special_close(exchange: str, date: Any) -> None:
    """
    Clear a special close from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to clear the day.
    date : Any
        The date to clear. Must be convertible to pandas.Timestamp.

    Returns
    -------
    None
    """
    _reset_day(exchange, date, DayType.SPECIAL_CLOSE)


def add_quarterly_expiry(exchange: str, date: Any, name: str = "Quarterly Expiry", strict: bool = False) -> None:
    """
    Add a quarterly expiry to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    name : str
        The name of the quarterly expiry.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after adding the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"name": name}, DayType.QUARTERLY_EXPIRY, strict=strict)


def remove_quarterly_expiry(exchange: str, date: Any, strict: bool = False) -> None:
    """
    Remove a quarterly expiry from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after removing the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after removing the day.
    """
    _remove_day(exchange, date, DayType.QUARTERLY_EXPIRY, strict=strict)


def reset_quarterly_expiry(exchange: str, date: Any) -> None:
    """
    Clear a quarterly expiry from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to clear the day.
    date : Any
        The date to clear. Must be convertible to pandas.Timestamp.

    Returns
    -------
    None
    """
    _reset_day(exchange, date, DayType.QUARTERLY_EXPIRY)


def add_monthly_expiry(exchange: str, date: Any, name: str = "Monthly Expiry", strict: bool = False) -> None:
    """
    Add a monthly expiry to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : Any
        The date to add. Must be convertible to pandas.Timestamp.
    name : str
        The name of the monthly expiry.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after adding the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"name": name}, DayType.MONTHLY_EXPIRY, strict=strict)

    
def remove_monthly_expiry(exchange: str, date: Any, strict: bool = False) -> None:
    """
    Remove a monthly expiry from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : Any
        The date to remove. Must be convertible to pandas.Timestamp.
    strict : bool
        Whether to raise an error if the changeset for the exchange would be inconsistent after removing the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after removing the day.
    """
    _remove_day(exchange, date, DayType.MONTHLY_EXPIRY, strict=strict)


def reset_monthly_expiry(exchange: str, date: Any) -> None:
    """
    Clear a monthly expiry from an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to clear the day.
    date : Any
        The date to clear. Must be convertible to pandas.Timestamp.

    Returns
    -------
    None
    """
    _reset_day(exchange, date, DayType.MONTHLY_EXPIRY)


@_with_changeset
def _reset_calendar(cs: ChangeSet) -> None:
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
    return cs.clear()


def reset_calendar(exchange: str) -> None:
    """
    Reset an exchange calendar to its original state.

    Parameters
    ----------
    exchange : str
        The exchange key for which to reset the calendar.

    Returns
    -------
    None
    """
    _reset_calendar(exchange)


@_with_changeset
def _update_calendar(_: ChangeSet, changes: dict) -> ChangeSet:
    return ChangeSet(**changes)


def update_calendar(exchange: str, changes: dict) -> None:
    """
    Apply changes to an exchange calendar.

    Parameters
    ----------
    changes : dict
        The changes to apply.

    Returns
    -------
    None
    """
    _update_calendar(exchange, changes)


# Declare public names.
__all__ = ["apply_extensions", "remove_extensions", "register_extension", "extend_class", "DayType", "add_day",
           "remove_day", "reset_day""", "DaySpec", "DayWithTimeSpec", "add_holiday", "remove_holiday", "reset_holiday",
           "add_special_close", "remove_special_close", "reset_special_close", "add_special_open",
           "remove_special_open", "reset_special_open", "add_quarterly_expiry", "remove_quarterly_expiry",
           "reset_quarterly_expiry", "add_monthly_expiry", "remove_monthly_expiry", "reset_monthly_expiry",
           "reset_calendar", "update_calendar", "ExtendedExchangeCalendar", "ExchangeCalendarExtensions"]

__version__ = None

try:
    from importlib.metadata import version
    # get version from installed package
    __version__ = version("exchange_calendars_extensions")
except ImportError:
    pass

if __version__ is None:
    try:
        # if package not installed, get version as set when package built.
        from ._version import version
    except Exception:
        # If package not installed and not built, leave __version__ as None
        pass
    else:
        __version__ = version

del version
