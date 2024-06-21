import functools
from typing import Callable, Union

from exchange_calendars import (
    calendar_utils,
    register_calendar_type,
    get_calendar_names,
)
from pydantic import validate_call, BaseModel, conint
from typing_extensions import ParamSpec, Concatenate

from exchange_calendars_extensions.api.changes import (
    ChangeSet,
    ChangeSetDict,
    DayType,
    DateLike,
    DayPropsLike,
    Tags,
    TimeLike,
    DayMeta,
)
from exchange_calendars_extensions.core.holiday_calendar import (
    extend_class,
    ExtendedExchangeCalendar,
    ExchangeCalendarExtensions,
)

# Dictionary that maps from exchange key to ExchangeCalendarChangeSet. Contains all changesets to apply when creating a
# new calendar instance. This dictionary should only ever contain non-empty changesets. If a changeset becomes empty,
# the corresponding entry should just be removed.
_changesets: dict[str, ChangeSet] = dict()


class ExtensionSpec(BaseModel, arbitrary_types_allowed=True):
    """Specifies how to derive an extended calendar class from a vanilla calendar class."""

    # The day of the week on which options expire. If None, expiry days are not supported.
    day_of_week_expiry: Union[conint(ge=0, le=6), None] = None


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

    def get_changeset_fn(name: str) -> Callable[[], ChangeSet]:
        """Returns a function that returns the changeset for the given exchange key.

        Parameters
        ----------
        name : str
            The exchange key for which to return the changeset.

        Returns
        -------
        Callable[[], ChangeSet]
            The function that returns the changeset.
        """

        def fn() -> ChangeSet:
            return _changesets.get(name)

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


def register_extension(name: str, day_of_week_expiry: Union[int, None] = None) -> None:
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
        cs: ChangeSet = _changesets.get(exchange, ChangeSet())

        # Call wrapped function with changeset as first positional argument.
        cs = f(cs, *args, **kwargs)

        if cs is not None:
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
def _add_day(cs: ChangeSet, date: DateLike, props: DayPropsLike) -> ChangeSet:
    """
    Add a day of a given type to the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset to which to add the day.
    date : TimestampLike
        The date to add. Must be convertible to pandas.Timestamp.
    props : DayPropsLike
        The properties of the day to add.

    Returns
    -------
    ChangeSet
        The changeset with the added day.

    Raises
    ------
    ValueError
        If the changeset would be inconsistent after adding the day.
    """
    return cs.add_day(date, props)


@validate_call(config={"arbitrary_types_allowed": True})
def add_day(exchange: str, date: DateLike, props: DayPropsLike) -> None:
    """
    Add a day of a given type to the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : TimestampLike
        The date to add. Must be convertible to pandas.Timestamp.
    props : Union[DaySpec, DaySpecWithTime, dict]
        The properties to add for the day. Must match the properties required by the given day type.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, props)


@_with_changeset
def _remove_day(cs: ChangeSet, date: DateLike) -> ChangeSet:
    """
    Remove a day of a given type from the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset from which to remove the day.
    date : TimestampLike
        The date to remove. Must be convertible to pandas.Timestamp.

    Returns
    -------
    ChangeSet
        The changeset with the removed day.
    """
    return cs.remove_day(date)


@validate_call(config={"arbitrary_types_allowed": True})
def remove_day(exchange: str, date: DateLike) -> None:
    """
    Remove a day of a given type from the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to remove the day.
    date : TimestampLike
        The date to remove. Must be convertible to pandas.Timestamp.

    Returns
    -------
    None
    """
    _remove_day(exchange, date)


@_with_changeset
def _set_tags(cs: ChangeSet, date: DateLike, tags: Tags) -> ChangeSet:
    """
    Set tags for a given day in the given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset where to set the tags.
    date : TimestampLike
        The date for which to set the tags.
    tags : Tags
        The tags to set.

    Returns
    -------
    ChangeSet
        The changeset with the given tags set for the given day.
    """
    return cs.set_tags(date, tags)


@validate_call(config={"arbitrary_types_allowed": True})
def set_tags(exchange: str, date: DateLike, tags: Tags) -> None:
    """
    Set tags for a given day in the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange for which to set the tags.
    date : TimestampLike
        The date for which to set the tags.
    tags : Tags
        The tags to set.

    Returns
    -------
    None
    """
    _set_tags(exchange, date, tags)


@_with_changeset
def _set_comment(cs: ChangeSet, date: DateLike, comment: Union[str, None]) -> ChangeSet:
    """
    Set comment for a given day in the given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset where to set the tags.
    date : TimestampLike
        The date for which to set the tags.
    comment : str
        The comment to set.

    Returns
    -------
    ChangeSet
        The changeset with the given comment set for the given day.
    """
    return cs.set_comment(date, comment)


@validate_call(config={"arbitrary_types_allowed": True})
def set_comment(exchange: str, date: DateLike, comment: Union[str, None]) -> None:
    """
    Set tags for a given day in the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange for which to set the tags.
    date : TimestampLike
        The date for which to set the tags.
    comment : str
        The comment to set.

    Returns
    -------
    None
    """
    _set_comment(exchange, date, comment)


@_with_changeset
def _set_meta(cs: ChangeSet, date: DateLike, meta: Union[DayMeta, None]) -> ChangeSet:
    """
    Set metadata for a given day in the given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset where to set the tags.
    date : TimestampLike
        The date for which to set the tags.
    meta : DayMeta
        The metadata to set.

    Returns
    -------
    ChangeSet
        The changeset with the given metadata set for the given day.
    """
    return cs.set_meta(date, meta)


@validate_call(config={"arbitrary_types_allowed": True})
def set_meta(exchange: str, date: DateLike, meta: Union[DayMeta, None]) -> None:
    """
    Set metadata for a given day in the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange for which to set the tags.
    date : TimestampLike
        The date for which to set the tags.
    meta : DayMeta
        The metadata to set.

    Returns
    -------
    None
    """
    _set_meta(exchange, date, meta)


@_with_changeset
def _reset_day(cs: ChangeSet, date: DateLike, include_tags: bool) -> ChangeSet:
    """
    Clear a day of a given type from the changeset for a given exchange calendar.

    Parameters
    ----------
    cs : ChangeSet
        The changeset from which to clear the day.
    date : TimestampLike
        The date to clear. Must be convertible to pandas.Timestamp.
    include_tags : bool
        Whether to also clear the tags for the day.

    Returns
    -------
    ChangeSet
        The changeset with the cleared day.
    """
    return cs.clear_day(date, include_meta=include_tags)


@validate_call(config={"arbitrary_types_allowed": True})
def reset_day(exchange: str, date: DateLike, include_tags: bool = False) -> None:
    """
    Clear a day of a given type from the given exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to clear the day.
    date : TimestampLike
        The date to clear. Must be convertible to pandas.Timestamp.
    include_tags : bool
        Whether to also clear the tags for the day. Defaults to False.

    Returns
    -------
    None
    """
    _reset_day(exchange, date, include_tags=include_tags)


def add_holiday(exchange: str, date: DateLike, name: str = "Holiday") -> None:
    """
    Add a holiday to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : TimestampLike
        The date to add. Must be convertible to pandas.Timestamp.
    name : str
        The name of the holiday.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"type": DayType.HOLIDAY, "name": name})


def add_special_open(
    exchange: str, date: DateLike, time: TimeLike, name: str = "Special Open"
) -> None:
    """
    Add a special open to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : TimestampLike
        The date to add. Must be convertible to pandas.Timestamp.
    time : TimeLike
        The time of the special open. If a string, must be in the format 'HH:MM' or 'HH:MM:SS'.
    name : str
        The name of the special open.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"type": DayType.SPECIAL_OPEN, "name": name, "time": time})


def add_special_close(
    exchange: str, date: DateLike, time: TimeLike, name: str = "Special Close"
) -> None:
    """
    Add a special close to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : TimestampLike
        The date to add. Must be convertible to pandas.Timestamp.
    time : TimeLike
        The time of the special close. If a string, must be in the format 'HH:MM' or 'HH:MM:SS'.
    name : str
        The name of the special close.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(
        exchange, date, {"type": DayType.SPECIAL_CLOSE, "name": name, "time": time}
    )


def add_quarterly_expiry(
    exchange: str, date: DateLike, name: str = "Quarterly Expiry"
) -> None:
    """
    Add a quarterly expiry to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : TimestampLike
        The date to add. Must be convertible to pandas.Timestamp.
    name : str
        The name of the quarterly expiry.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"type": DayType.QUARTERLY_EXPIRY, "name": name})


def add_monthly_expiry(
    exchange: str, date: DateLike, name: str = "Monthly Expiry"
) -> None:
    """
    Add a monthly expiry to an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to add the day.
    date : TimestampLike
        The date to add. Must be convertible to pandas.Timestamp.
    name : str
        The name of the monthly expiry.

    Returns
    -------
    None

    Raises
    ------
    ValidationError
        If strict is True and the changeset for the exchange would be inconsistent after adding the day.
    """
    _add_day(exchange, date, {"type": DayType.MONTHLY_EXPIRY, "name": name})


@_with_changeset
def _reset_calendar(cs: ChangeSet, include_tags: bool) -> ChangeSet:
    """
    Reset an exchange calendar to its original state.

    Parameters
    ----------
    cs : ChangeSet
        The changeset to reset.

    Returns
    -------
    ChangeSet
        The reset changeset.
    """
    return cs.clear(include_meta=include_tags)


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
    _reset_calendar(exchange, include_tags=True)


def reset_all_calendars() -> None:
    """
    Reset all exchange calendars to their original states.

    Returns
    -------
    None
    """
    # Just clear the dict of changesets.
    _changesets.clear()


@_with_changeset
def _update_calendar(_: ChangeSet, changes: ChangeSet) -> ChangeSet:
    return changes


@validate_call
def update_calendar(exchange: str, changes: Union[ChangeSet, dict]) -> None:
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
    _update_calendar(exchange, changes)


def get_changes_for_calendar(exchange: str) -> Union[ChangeSet, None]:
    """
    Get the changes for an exchange calendar.

    Parameters
    ----------
    exchange : str
        The exchange key for which to get the changes.

    Returns
    -------
    ChangeSet
        The changeset for the given exchange, or None, if no changes have been registered.
    """
    cs: Union[ChangeSet, None] = _changesets.get(exchange, None)

    if cs is not None:
        cs = cs.model_copy(deep=True)

    return cs


def get_changes_for_all_calendars() -> ChangeSetDict:
    """
    Get the changes for all exchange calendars.

    Returns
    -------
    dict
        The changes for all exchange calendars.
    """
    return ChangeSetDict({k: v.model_copy(deep=True) for k, v in _changesets.items()})


# Declare public names.
__all__ = [
    "apply_extensions",
    "remove_extensions",
    "register_extension",
    "extend_class",
    "DayType",
    "add_day",
    "remove_day",
    "reset_day",
    "DayPropsLike",
    "add_holiday",
    "add_special_close",
    "add_special_open",
    "add_quarterly_expiry",
    "add_monthly_expiry",
    "set_meta",
    "reset_calendar",
    "reset_all_calendars",
    "update_calendar",
    "get_changes_for_calendar",
    "get_changes_for_all_calendars",
    "ChangeSet",
    "ExtendedExchangeCalendar",
    "ExchangeCalendarExtensions",
]

__version__ = None

try:
    from importlib.metadata import version

    # get version from installed package
    __version__ = version("exchange_calendars_extensions")
    del version
except ImportError:
    pass

if __version__ is None:
    try:
        # if package not installed, get version as set when package built.
        from .version import version
    except Exception:
        # If package not installed and not built, leave __version__ as None
        pass
    else:
        __version__ = version
        del version
