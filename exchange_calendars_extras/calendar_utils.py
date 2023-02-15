import typing
from typing import Literal

from exchange_calendars.calendar_helpers import Date
from exchange_calendars.calendar_utils import (
    clear_calendars as clear_calendars_upstream,
    deregister_calendar as deregister_calendar_upstream,
    get_calendar as get_calendar_upstream,
    get_calendar_names as get_calendar_names_upstream,
    register_calendar as register_calendar_upstream,
    register_calendar_alias as register_calendar_alias_upstream,
    register_calendar_type as register_calendar_type_upstream,
    resolve_alias as resolve_alias_upstream,
    names_to_aliases as names_to_aliases_upstream,
    aliases_to_names as aliases_to_names_upstream,
)
from exchange_calendars import ExchangeCalendar


class ExchangeCalendarDispatcher(object):
    """
    A class for dispatching and caching extended exchange calendars.

    Methods of a global instance of this class can be accessed directly
    from exchange_calendars, for example `exchange_calendars_extras.get_calendar`.

    Parameters
    ----------
    calendars : dict[str -> ExchangeCalendar]
        Initial set of calendars.
    calendar_factories : dict[str -> function]
        Factories for lazy calendar creation.
    aliases : dict[str -> str]
        Calendar name aliases.
    """

    def __init__(self, calendars, calendar_factories, aliases):
        #self._calendars = calendars
        #self._calendar_factories = dict(calendar_factories)
        #self._aliases = dict(aliases)
        # key: factory name, value: (calendar, dict of calendar kwargs)
        #self._factory_output_cache: dict(str, tuple(ExchangeCalendar, dict)) = {}
        ...

    def _fabricate(self, name: str, **kwargs) -> ExchangeCalendar:
        # """Fabricate calendar with `name` and `**kwargs`."""
        # try:
        #     factory = self._calendar_factories[name]
        # except KeyError as e:
        #     raise InvalidCalendarName(calendar_name=name) from e
        # calendar = factory(**kwargs)
        # self._factory_output_cache[name] = (calendar, kwargs)
        # return calendar
       ...

    def _get_cached_factory_output(
        self, name: str, **kwargs
    ) -> ExchangeCalendar | None:
        # """Get calendar from factory output cache.
        #
        # Return None if `name` not in cache or `name` in cache although
        # calendar got with kwargs other than `**kwargs`.
        # """
        # calendar, calendar_kwargs = self._factory_output_cache.get(name, (None, None))
        # if calendar is not None and calendar_kwargs == kwargs:
        #     return calendar
        # else:
        #     return None
        ...

    def get_calendar(
        self,
        name: str,
        start: Date | None = None,
        end: Date | None = None,
        side: Literal["left", "right", "both", "neither"] | None = None,
    ) -> ExchangeCalendar:
        """Get exchange calendar with a given name.

        Parameters
        ----------
        name
            Name of the ExchangeCalendar to get, for example 'XNYS'.

        The following arguments will be passed to the calendar factory.
        These arguments can only be passed if `name` is registered as a
        calendar factory (either by having been included to
        `calendar_factories` passed to the dispatcher's constructor or
        having been subsequently registered via the
        `register_calendar_type` method).

        start : default: as default for calendar factory
            First calendar session will be `start`, if `start` is a
            session, or first session after `start`. Cannot be earlier than
            any date returned by the respective calendar class method
            `bound_min`.

        end : default: as default for calendar factory
            Last calendar session will be `end`, if `end` is a session, or
            last session before `end`. Cannot be later than any date
            returned by the respective calendar class method `bound_max`.

        side : default: as default for calendar factory
            Define which of session open/close and break start/end should
                be treated as a trading minute:
            "left" - treat session open and break_start as trading minutes,
                do not treat session close or break_end as trading minutes.
            "right" - treat session close and break_end as trading minutes,
                do not treat session open or break_start as tradng minutes.
            "both" - treat all of session open, session close, break_start
                and break_end as trading minutes.
            "neither" - treat none of session open, session close,
                break_start or break_end as trading minutes.

        Returns
        -------
        ExtendedExchangeCalendar
            Requested calendar.

        Raises
        ------
        InvalidCalendarName
            If `name` does not represent a registered calendar.

        ValueError
            If `start`, `end` or `side` are received although `name` is a
            registered calendar (as opposed to a calendar factory).

            If `start` or `end` are received although do not parse as a
            date that could represent a session.
        """
        # # will raise InvalidCalendarName if name not valid
        # name = self.resolve_alias(name)
        #
        # kwargs = {}
        # for k, v in zip(["start", "end", "side"], [start, end, side]):
        #     if v is not None:
        #         kwargs[k] = v
        #
        # if name in self._calendars:
        #     if kwargs:
        #         raise ValueError(
        #             f"Receieved calendar arguments although {name} is registered"
        #             f" as a specific instance of class"
        #             f" {self._calendars[name].__class__}, not as a calendar factory."
        #         )
        #     else:
        #         return self._calendars[name]
        #
        # if kwargs.get("start"):
        #     kwargs["start"] = parse_date(kwargs["start"], "start", raise_oob=False)
        # else:
        #     kwargs["start"] = None
        # if kwargs.get("end"):
        #     kwargs["end"] = parse_date(kwargs["end"], "end", raise_oob=False)
        # else:
        #     kwargs["end"] = None
        #
        # cached = self._get_cached_factory_output(name, **kwargs)
        # return cached if cached is not None else self._fabricate(name, **kwargs)
        ...

    def get_calendar_names(
        self, include_aliases: bool = True, sort: bool = True
    ) -> list[str]:
        """Return all canoncial calendar names and, optionally, aliases.

        Parameters
        ----------
        include_aliases : default: True
            True to include calendar aliases.
            False to return only canonical calendar names.

        sort : default: True
            Return calendar names sorted alphabetically.

        Returns
        -------
        list of str
            List of canonical calendar names and, optionally, aliases.

        See Also
        --------
        names_to_aliases : Mapping of cononcial names to aliases.
        aliases_to_names : Mapping of aliases to canoncial names.
        resolve_alias : Resolve single alias to a canonical name.
        """
        return get_calendar_names_upstream(include_aliases=include_aliases, sort=sort)

    def has_calendar(self, name):
        """
        Do we have (or have the ability to make) a calendar with ``name``?
        """
        return (
            name in self._calendars
            or name in self._calendar_factories
            or name in self._aliases
        )

    def register_calendar(self, name, calendar, force=False):
        """
        Registers a calendar for retrieval by the get_calendar method.

        Parameters
        ----------
        name: str
            The key with which to register this calendar.
        calendar: ExchangeCalendar
            The calendar to be registered for retrieval.
        force : bool, optional
            If True, old calendars will be overwritten on a name collision.
            If False, name collisions will raise an exception.
            Default is False.

        Raises
        ------
        CalendarNameCollision
            If a calendar is already registered with the given calendar's name.
        """
        register_calendar_upstream(name, calendar, force=force)

    def register_calendar_type(self, name, calendar_type, force=False):
        """
        Registers a calendar by type.

        This is useful for registering a new calendar to be lazily instantiated
        at some future point in time.

        Parameters
        ----------
        name: str
            The key with which to register this calendar.
        calendar_type: type
            The type of the calendar to register.
        force : bool, optional
            If True, old calendars will be overwritten on a name collision.
            If False, name collisions will raise an exception.
            Default is False.

        Raises
        ------
        CalendarNameCollision
            If a calendar is already registered with the given calendar's name.
        """
        register_calendar_type_upstream(name, calendar_type, force=force)

    def register_calendar_alias(self, alias, real_name, force=False):
        """
        Register an alias for a calendar.

        This is useful when multiple exchanges should share a calendar, or when
        there are multiple ways to refer to the same exchange.

        After calling ``register_alias('alias', 'real_name')``, subsequent
        calls to ``get_calendar('alias')`` will return the same result as
        ``get_calendar('real_name')``.

        Parameters
        ----------
        alias : str
            The name to be used to refer to a calendar.
        real_name : str
            The canonical name of the registered calendar.
        force : bool, optional
            If True, old calendars will be overwritten on a name collision.
            If False, name collisions will raise an exception.
            Default is False.
        """
        register_calendar_alias_upstream(alias, real_name, force=force)

    def resolve_alias(self, name: str):
        """Resolve an alias to cononcial name of corresponding calendar.

        A cononical name will resolve to itself.

        Parameters
        ----------
        name :
            Alias or canoncial name corresponding to a calendar.

        Returns
        -------
        canonical_name : str
            Canonical name of calendar that would be created for `name`.

        Raises
        ------
        InvalidCalendarName
            If `name` is not an alias or canonical name of any registered
            calendar.

        See Also
        --------
        aliases_to_names : Mapping of aliases to canoncial names.
        names_to_aliases : Mapping of cononcial names to aliases.
        """
        return resolve_alias_upstream(name)

    def aliases_to_names(self) -> dict[str, str]:
        """Return dictionary mapping aliases to canonical names.

        Returns
        -------
        dict of {str, str}
            Dictionary mapping aliases to canoncial name of corresponding
            calendar.

        See Also
        --------
        resolve_alias : Resolve single alias to a canonical name.
        names_to_aliases : Mapping of cononcial names to aliases.
        """
        return aliases_to_names_upstream()

    def names_to_aliases(self) -> dict[str, list[str]]:
        """Return mapping of canonical calendar names to associated aliases.

        Returns
        -------
        dict of {str, list of str}
            Dictionary mapping canonical calendar names to any associated
            aliases.

        See Also
        --------
        aliases_to_names : Mapping of aliases to canoncial names.
        """
        return names_to_aliases_upstream()

    def deregister_calendar(self, name):
        """
        If a calendar is registered with the given name, it is de-registered.

        Parameters
        ----------
        name : str
            The name of the calendar to be deregistered.
        """
        deregister_calendar_upstream(name)

    def clear_calendars(self):
        """
        Deregisters all current registered calendars
        """
        clear_calendars_upstream()


# We maintain a global calendar dispatcher so that users can just do
# `register_calendar('my_calendar', calendar) and then use `get_calendar`
# without having to thread around a dispatcher.
global_calendar_dispatcher = ExchangeCalendarDispatcher(
    None, #calendars={},
    None, #calendar_factories=_default_calendar_factories,
    None,# aliases=_default_calendar_aliases,
)

get_calendar = global_calendar_dispatcher.get_calendar
get_calendar_names = global_calendar_dispatcher.get_calendar_names
clear_calendars = global_calendar_dispatcher.clear_calendars
deregister_calendar = global_calendar_dispatcher.deregister_calendar
register_calendar = global_calendar_dispatcher.register_calendar
register_calendar_type = global_calendar_dispatcher.register_calendar_type
register_calendar_alias = global_calendar_dispatcher.register_calendar_alias
resolve_alias = global_calendar_dispatcher.resolve_alias
aliases_to_names = global_calendar_dispatcher.aliases_to_names
names_to_aliases = global_calendar_dispatcher.names_to_aliases
