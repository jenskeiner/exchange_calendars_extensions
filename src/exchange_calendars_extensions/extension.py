from typing import Annotated

from pydantic import BaseModel, Field

WeekDayInt = Annotated[int, Field(ge=0, le=6)]


class ExtensionSpec(BaseModel, arbitrary_types_allowed=True):
    """Specifies how to derive an extended calendar class from a vanilla calendar class."""

    # The day of the week on which options expire. If None, expiry days are not supported.
    day_of_week_expiry: WeekDayInt | None = None
