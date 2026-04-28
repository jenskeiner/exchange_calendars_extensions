from collections.abc import Callable
from dataclasses import dataclass, field

from .changes import ChangeSet
from .extension import ExtensionSpec
from .holiday_calendar import ExtendedExchangeCalendar


@dataclass
class _State:
    # Dictionary that maps from exchange key to ConsolidatedChangeSet. Contains all changesets to apply when creating a new
    # calendar instance. This dictionary should only ever contain non-empty changesets. If a changeset becomes empty, the
    # corresponding entry should just be removed.
    changesets: dict[str, ChangeSet] = field(default_factory=dict)
    # Internal dictionary containing the original calendar classes.
    original_classes: dict[str, type[ExtendedExchangeCalendar]] = field(
        default_factory=dict
    )
    extensions: dict[str, ExtensionSpec] = field(
        default_factory=lambda: {
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
    )
    register_calendar_type_orig: Callable | None = None


_state = _State()


def get_state() -> _State:
    return _state
