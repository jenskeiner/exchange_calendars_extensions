import functools
from collections.abc import Callable
from typing import Annotated, Concatenate, Literal

from exchange_calendars import (
    calendar_utils,
    get_calendar_names,
    register_calendar_type,
)
from pydantic import BaseModel, Field, validate_call
from typing_extensions import ParamSpec

from .changes import (
    CLEAR,
    BusinessDaySpec,
    ChangeSet,
    Clear,
    ConsolidatedChangeSet,
    DayAction,
    DayChange,
    DaySpec,
    NonBusinessDaySpec,
    consolidate,
)
from .datetime import (
    DateLike,
    DateLikeInput,
)
from .holiday_calendar import (
    ExchangeCalendarExtensions,
    ExtendedExchangeCalendar,
    extend_class,
)
from .util import copy_changeset

# Dictionary that maps from exchange key to ConsolidatedChangeSet. Contains all changesets to apply when creating a new
# calendar instance. This dictionary should only ever contain non-empty changesets. If a changeset becomes empty, the
# corresponding entry should just be removed.
_changesets: dict[str, ConsolidatedChangeSet] = {}


WeekDayInt = Annotated[int, Field(ge=0, le=6)]


class ExtensionSpec(BaseModel, arbitrary_types_allowed=True):
    """Specifies how to derive an extended calendar class from a vanilla calendar class."""

    # The day of the week on which options expire. If None, expiry days are not supported.
    day_of_week_expiry: WeekDayInt | None = None


# Internal dictionary that specifies how to derive extended calendars for specific exchanges.
_extensions: dict[str, ExtensionSpec] = {
    "ASEX": ExtensionSpec(day_of_week_expiry=4),
    "XAMS": ExtensionSpec(day_of_week_expiry=4),
    "XBRU": ExtensionSpec(day_of_week_expiry=4),
    "XBUD": ExtensionSpec(day_of_week_expiry=4),
    "XCSE": ExtensionSpec(day_of_week_expiry=4),
    "XDUB": ExtensionSpec(day_of_week_expiry=4),
    "XETR": ExtensionSpec(day_of_week_expiry=4),
    "XHEL": ExtensionSpec(day_of_week_expiry=4),
    "XIST": ExtensionSpec(day_of_week_expiry=4),
    "XJSE": ExtensionSpec(day_of_week_expiry=3),
    "XLIS": ExtensionSpec(day_of_week_expiry=4),
    "XLON": ExtensionSpec(day_of_week_expiry=4),
    "XMAD": ExtensionSpec(day_of_week_expiry=4),
    "XMIL": ExtensionSpec(day_of_week_expiry=4),
    "XNYS": ExtensionSpec(day_of_week_expiry=4),
    "XOSL": ExtensionSpec(day_of_week_expiry=4),
    "XPAR": ExtensionSpec(day_of_week_expiry=4),
    "XPRA": ExtensionSpec(day_of_week_expiry=4),
    "XSTO": ExtensionSpec(day_of_week_expiry=4),
    "XSWX": ExtensionSpec(day_of_week_expiry=4),
    "XTAE": ExtensionSpec(day_of_week_expiry=4),
    "XTSE": ExtensionSpec(day_of_week_expiry=4),
    "XWAR": ExtensionSpec(day_of_week_expiry=4),
    "XWBO": ExtensionSpec(day_of_week_expiry=4),
}


# Internal dictionary containing the original calendar classes.
_original_classes = dict()


def apply_extensions() -> None:
    """
    Apply extensions to exchange_calendars.

    This registers all extended calendars in exchange_calendars, replacing the respective vanilla calendars.

    This function is idempotent. If extensions have already been applied, this function does nothing.
    """
    if len(_original_classes) > 0:
        # Extensions have already been applied.
        return

    # Get all calendar names, including aliases.
    calendar_names = set(get_calendar_names())

    def get_changeset_fn(name: str) -> Callable[[], ConsolidatedChangeSet | None]:
        """Returns a function that returns the changeset for the given exchange key.

        Parameters
        ----------
        name : str
            The exchange key for which to return the changeset.

        Returns
        -------
        Callable[[], CalendarChanges]
            The function that returns the changeset and removed days.
        """

        def fn() -> ConsolidatedChangeSet | None:
            cs = _changesets.get(name)
            return cs

        return fn

    # Create and register extended calendar classes for all calendars for which no explicit rules have been defined.
    for k in calendar_names - set(_extensions.keys()):
        # Get the original class.
        cls = calendar_utils.global_calendar_dispatcher._calendar_factories.get(k)

        if cls is not None:
            # Store the original class for later use.
            _original_classes[k] = cls

            # Create extended class without support for expiry days.
            cls = extend_class(
                cls, day_of_week_expiry=None, changeset_provider=get_changeset_fn(k)
            )

            # Register extended class.
            register_calendar_type(k, cls, force=True)

            # Remove original class from factory cache.
            _remove_calendar_from_factory_cache(k)

    # Create and register extended calendar classes for all calendars for which explicit rules have been defined.
    for k, v in _extensions.items():
        # Get the original class.
        cls = calendar_utils.global_calendar_dispatcher._calendar_factories.get(k)

        if cls is not None:
            # Get the day of the week for expiry days.
            day_of_week_expiry = v.day_of_week_expiry

            # Store the original class for later use.
            _original_classes[k] = cls

            # Create extended class with support for expiry days.
            cls = extend_class(
                cls,
                day_of_week_expiry=day_of_week_expiry,
                changeset_provider=get_changeset_fn(k),
            )

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

    # Clear original classes.
    _original_classes.clear()


def register_extension(name: str, day_of_week_expiry: int | None = None) -> None:
    """
    Register an extended calendar class for a given exchange key and a given base class.

    This creates and then registers an extended calendar class based on the given class, with support for all
    additional properties of ExtendedExchangeCalendar. Expiry days are on the third instance of the given day of the
    week in each month. The extended class also supports programmatic modifications; see e.g. add_holiday().

    Parameters
    ----------
    name : str
        The exchange key for which to register the extended calendar class.
    day_of_week_expiry : Optional[int]
        The day of the week on which options expire. If None, expiry days are not supported.

    Returns
    -------
    None
    """
    _extensions[name] = ExtensionSpec(day_of_week_expiry=day_of_week_expiry)


def _remove_calendar_from_factory_cache(name: str):
    """
    Remove a cached calendar instance for the given exchange key from the factory cache.

    Caveat: This function accesses the private attribute _factory_output_cache of the global calendar dispatcher.
    """
    # noinspection PyProtectedMember
    calendar_utils.global_calendar_dispatcher._factory_output_cache.pop(name, None)


P = ParamSpec("P")


def _with_changeset(
    f: Callable[Concatenate[ConsolidatedChangeSet, P], ConsolidatedChangeSet],
) -> Callable[Concatenate[str, P], None]:
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
        cs: ConsolidatedChangeSet = _changesets.get(exchange, {})

        # Call wrapped function with changeset as first positional argument.
        cs = f(cs, *args, **kwargs)

        if cs:
            # Save changeset back to _changesets.
            _changesets[exchange] = cs
        else:
            # Remove changeset from _changesets.
            _changesets.pop(exchange, None)

        # Remove calendar for exchange key from factory cache.
        _remove_calendar_from_factory_cache(exchange)

        # Return result of wrapped function.
        return None

    return wrapper


@_with_changeset
def _change_day(
    cs: ConsolidatedChangeSet, date: DateLike, action: DayAction
) -> ConsolidatedChangeSet:
    """
    Add a day of a given type to the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ConsolidatedChangeSet
        The changeset to which to add the day.
    day : Day
        The day to add (BusinessDay or NonBusinessDay).

    Returns
    -------
    ConsolidatedChangeSet
        The changeset with the added day.

    Raises
    ------
    ValueError
        If the day type is not supported.
    """
    if isinstance(action, Clear):
        _ = cs.pop(date, None)
    else:
        assert isinstance(action, DayChange)
        # Get existing change for day, maybe.
        change0: DayChange | None = cs.get(date)
        cs[date] = action if not change0 else change0.merge(action)
    return cs


@validate_call
def change_day(exchange: str, date: DateLikeInput, action: DayAction) -> None:
    """
    Add a day of a given type to the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : Day
        The day to add (BusinessDay or NonBusinessDay).
    action : DayAction
        The change to apply to the day.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _change_day(exchange, date, action)


@_with_changeset
def _change_calendar(
    changes0: ConsolidatedChangeSet,
    changes: ChangeSet,
    mode: Literal["merge", "update", "replace"],
) -> ConsolidatedChangeSet:
    match mode:
        case "replace":
            return consolidate(changes)
        case "update":
            result = dict(changes0)
            for k, v in changes.items():
                result[k] = v
            return consolidate(result)
        case "merge":
            result = dict(changes0)
            for k, v in changes.items():
                if k not in result:
                    result[k] = v
                else:
                    v0: DayChange = result[k]
                    result[k] = v0.merge(v) if isinstance(v, DayChange) else CLEAR
            return consolidate(result)


@validate_call
def change_calendar(
    exchange: str,
    changes: ChangeSet,
    mode: Literal["merge", "update", "replace"] = "merge",
) -> None:
    """
    Apply changes to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to apply the changes.
    changes : ChangeSet
        The changes to apply.

    Returns
    -------
    None
    """
    _change_calendar(exchange, changes, mode)


def get_changes(exchange: str | None = None) -> ChangeSet | dict[str, ChangeSet] | None:
    """
    Get the changes for an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to get the changes.

    Returns
    -------
    ChangeSet | None
        The changeset for the given exchange, or None, if no changes have been registered.
    """
    if exchange is None:
        return {k: copy_changeset(v) for k, v in _changesets.items()}  # ty:ignore[invalid-argument-type]
    else:
        cs: ChangeSet | None = _changesets.get(exchange, None)  # ty:ignore[invalid-assignment]
        return copy_changeset(cs) if cs else None


def remove_changes(exchange: str | None = None) -> None:
    """
    Reset all exchange calendars to their original states.

    Returns
    -------
    None
    """
    if exchange is None:
        # Clear the dict of changesets.
        for k in _changesets.keys():
            _remove_calendar_from_factory_cache(k)
        _changesets.clear()
    else:
        cs = _changesets.pop(exchange, None)
        if cs:
            _remove_calendar_from_factory_cache(exchange)


# Declare public names.
__all__ = [
    "apply_extensions",
    "remove_extensions",
    "register_extension",
    "extend_class",
    "change_day",
    "change_calendar",
    "get_changes",
    "ExtendedExchangeCalendar",
    "ExchangeCalendarExtensions",
    "ChangeSet",
    "DaySpec",
    "CLEAR",
    "DayChange",
    "BusinessDaySpec",
    "NonBusinessDaySpec",
]
