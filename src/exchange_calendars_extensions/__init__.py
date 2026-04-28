import functools
from collections.abc import Callable
from typing import Any, Concatenate, overload

from exchange_calendars import (
    ExchangeCalendar,
    calendar_utils,
    get_calendar_names,
    register_calendar_type,
)
from pydantic import validate_call
from typing_extensions import ParamSpec

from exchange_calendars_extensions.util import consolidate, mode_multi_to_single

from .changes import (
    CLEAR,
    BusinessDaySpec,
    ChangeModeMulti,
    ChangeModeSingle,
    ChangeSet,
    ChangeSetDelta,
    ChangeSetDeltaDict,
    ChangeSetDict,
    Clear,
    DayAction,
    DayChange,
    DaySpec,
    NonBusinessDaySpec,
)
from .datetime import (
    DateLike,
    DateLikeInput,
    TimeLike,
    TimestampLike,
)
from .extension import ExtensionSpec
from .holiday_calendar import ExchangeCalendarExtensions, ExtendedExchangeCalendar
from .holiday_calendar import extend_class as extend_class_internal
from .state import get_state
from .util import copy_changeset


def apply_extensions() -> None:
    """
    Apply extensions to exchange_calendars.

    This registers all extended calendars in exchange_calendars, replacing the respective vanilla calendars.

    This function is idempotent. If extensions have already been applied, this function does nothing.
    """

    if len(get_state().original_classes) > 0:
        # Extensions have already been applied.
        return

    import exchange_calendars as ec
    import exchange_calendars.calendar_utils as ecu

    register_calendar_type_orig = ecu.register_calendar_type

    def _register_calendar_type(name, calendar_type, force=False):
        # The extended class to actually register.
        t: type[ExtendedExchangeCalendar] | None = None

        if force or not ecu.global_calendar_dispatcher.has_calendar(name):
            # Only set up extended class if upstream method will succeed.
            if issubclass(calendar_type, ExtendedExchangeCalendar):
                # Already an extended class.
                t = calendar_type
            else:
                # Create extended class.
                if name in get_state().extensions:
                    t = extend_class_internal(
                        calendar_type,
                        day_of_week_expiry=get_state()
                        .extensions[name]
                        .day_of_week_expiry,
                        changeset_provider=lambda self: get_state().changesets.get(
                            name
                        ),
                    )
                else:
                    t = extend_class_internal(
                        calendar_type,
                        day_of_week_expiry=None,
                        changeset_provider=lambda self: get_state().changesets.get(
                            name
                        ),
                    )

        register_calendar_type_orig(name, t, force)
        get_state().original_classes[name] = calendar_type

    ecu.register_calendar_type = _register_calendar_type  # ty:ignore[invalid-assignment]
    ec.register_calendar_type = _register_calendar_type  # ty:ignore[invalid-assignment]
    get_state().register_calendar_type_orig = register_calendar_type_orig

    def make_changeset_provider(
        name: str,
    ) -> Callable[[Any], ChangeSet | None]:
        """Return a ``_changeset_provider`` that looks up the given calendar name.

        The factory is required because the two loops below both bind a
        free variable ``k`` in a closure. Python closures capture by
        reference, so without this factory every provider would resolve
        ``k`` at call time to the last value iterated by the enclosing
        loops and fetch the wrong (or no) change-set.
        """
        return lambda self: get_state().changesets.get(name)

    # Get all calendar names, including aliases.
    calendar_names = set(get_calendar_names())

    # Create and register extended calendar classes for all calendars for which no explicit rules have been defined.
    for k in calendar_names - set(get_state().extensions.keys()):
        # Get the original class.
        cls = calendar_utils.global_calendar_dispatcher._calendar_factories.get(k)

        if cls is not None:
            # Store the original class for later use.
            get_state().original_classes[k] = cls

            # Create extended class without support for expiry days.
            cls = extend_class_internal(
                cls,
                day_of_week_expiry=None,
                changeset_provider=make_changeset_provider(k),
            )

            # Register extended class.
            register_calendar_type(k, cls, force=True)

            # Remove original class from factory cache.
            _remove_calendar_from_factory_cache(k)

    # Create and register extended calendar classes for all calendars for which explicit rules have been defined.
    for k, v in get_state().extensions.items():
        # Get the original class.
        cls = calendar_utils.global_calendar_dispatcher._calendar_factories.get(k)

        if cls is not None:
            # Get the day of the week for expiry days.
            day_of_week_expiry = v.day_of_week_expiry

            # Store the original class for later use.
            get_state().original_classes[k] = cls

            # Create extended class with support for expiry days.
            cls = extend_class_internal(
                cls,
                day_of_week_expiry=day_of_week_expiry,
                changeset_provider=make_changeset_provider(k),
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
    if len(get_state().original_classes) == 0:
        # Extensions have not been applied.
        return

    for k, v in get_state().original_classes.items():
        # Register original class.
        register_calendar_type(k, v, force=True)

        # Remove extended class from factory cache.
        _remove_calendar_from_factory_cache(k)

    # Clear original classes.
    get_state().original_classes.clear()

    import exchange_calendars as ec
    import exchange_calendars.calendar_utils as ecu

    ecu.register_calendar_type = get_state().register_calendar_type_orig  # ty:ignore[invalid-assignment]
    ec.register_calendar_type = get_state().register_calendar_type_orig  # ty:ignore[invalid-assignment]

    get_state().register_calendar_type_orig = None


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
    get_state().extensions[name] = ExtensionSpec(day_of_week_expiry=day_of_week_expiry)


def _remove_calendar_from_factory_cache(name: str):
    """
    Remove a cached calendar instance for the given exchange key from the factory cache.

    Caveat: This function accesses the private attribute _factory_output_cache of the global calendar dispatcher.
    """
    # noinspection PyProtectedMember
    calendar_utils.global_calendar_dispatcher._factory_output_cache.pop(name, None)


P = ParamSpec("P")


def _with_changeset(
    f: Callable[Concatenate[ChangeSet, P], ChangeSet],
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
        cs: ChangeSet = get_state().changesets.get(exchange, {})

        # Call wrapped function with changeset as first positional argument.
        cs = f(cs, *args, **kwargs)

        if cs:
            # Save changeset back to _changesets.
            get_state().changesets[exchange] = cs
        else:
            # Remove changeset from _changesets.
            get_state().changesets.pop(exchange, None)

        # Remove calendar for exchange key from factory cache.
        _remove_calendar_from_factory_cache(exchange)

        # Return result of wrapped function.
        return None

    return wrapper


@_with_changeset
def _change_day(cs: ChangeSet, date: DateLike, action: DayAction) -> ChangeSet:
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
    _change_day(exchange, DateLike(date), action)


def _change_calendar_update(current: ChangeSet, incoming: ChangeSetDelta) -> ChangeSet:
    r = dict(current)
    for k, v in incoming.items():
        if v is CLEAR:
            del r[k]
        elif isinstance(v, DayChange):
            r[k] = v
    return r


def _change_calendar_merge(current: ChangeSet, incoming: ChangeSetDelta) -> ChangeSet:
    r = dict(current)
    for k, v in incoming.items():
        if v is CLEAR:
            if k in r:
                del r[k]
        elif isinstance(v, DayChange):
            if k not in r:
                r[k] = v
            else:
                v0: DayChange = r[k]
                r[k] = v0.merge(v)
    return r


@_with_changeset
def _change_calendar(
    current: ChangeSet,
    incoming: ChangeSetDelta,
    mode: ChangeModeSingle,
) -> ChangeSet:
    match mode:
        case "replace":
            return consolidate(incoming)
        case "update":
            return _change_calendar_update(current, incoming)
        case "merge":
            return _change_calendar_merge(current, incoming)
        case _:
            raise ValueError(f"Invalid mode: {mode}")


@validate_call
def change_calendar(
    exchange: str,
    changeset: ChangeSetDelta,
    mode: ChangeModeSingle = "merge",
) -> None:
    """
    Apply changes to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to apply the changes.
    changeset : ChangeSet
        The changes to apply.

    Returns
    -------
    None
    """
    _change_calendar(exchange, changeset, mode)


@validate_call
def change_calendars(
    changeset_dict: ChangeSetDeltaDict,
    mode: ChangeModeMulti = "merge",
) -> None:
    """
    Apply changes to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to apply the changes.
    changeset_dict : ChangeSet
        The changes to apply.

    Returns
    -------
    None
    """
    if mode == "replace_all":
        remove_changes()

    mode0 = mode_multi_to_single(mode)

    for k, v in changeset_dict.items():
        _change_calendar(k, v, mode0)


@overload
def get_changes(
    exchange: None = None,
) -> dict[str, ChangeSet]: ...


@overload
def get_changes(
    exchange: str,
) -> ChangeSet | None: ...


def get_changes(
    exchange: str | None = None,
) -> dict[str, ChangeSet] | ChangeSet | None:
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
        return {k: copy_changeset(v) for k, v in get_state().changesets.items()}
    else:
        cs: ChangeSet | None = get_state().changesets.get(exchange, None)
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
        for k in get_state().changesets.keys():
            _remove_calendar_from_factory_cache(k)
        get_state().changesets.clear()
    else:
        cs = get_state().changesets.pop(exchange, None)
        if cs:
            _remove_calendar_from_factory_cache(exchange)


def extend_class(cls: type[ExchangeCalendar], day_of_week_expiry: int | None = None):
    return extend_class_internal(
        cls,
        day_of_week_expiry=day_of_week_expiry,
        changeset_provider=None,
    )


# Declare public names.
__all__ = [
    "apply_extensions",
    "remove_extensions",
    "register_extension",
    "change_day",
    "change_calendar",
    "change_calendars",
    "get_changes",
    "ExtendedExchangeCalendar",
    "ExchangeCalendarExtensions",
    "ChangeSetDelta",
    "ChangeSet",
    "ChangeSetDeltaDict",
    "ChangeSetDict",
    "DaySpec",
    "CLEAR",
    "DayChange",
    "BusinessDaySpec",
    "NonBusinessDaySpec",
    "extend_class",
    "ChangeModeSingle",
    "ChangeModeMulti",
    "TimestampLike",
    "DateLike",
    "TimeLike",
]
