from __future__ import annotations

import abc
from collections import OrderedDict
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, model_validator
from pydantic.experimental.missing_sentinel import MISSING
from typing_extensions import Self

from .datetime import DateLike, TimeLike


class BaseDaySpec(BaseModel, abc.ABC):
    @abc.abstractmethod
    def merge(self, other):
        pass


class NonBusinessDaySpec(BaseDaySpec):
    business_day: Literal[False] = False
    weekend_day: bool | MISSING = MISSING
    holiday: bool | MISSING = MISSING

    @model_validator(mode="after")
    def check_weekend_or_holiday(self) -> Self:
        if not ((self.weekend_day is True) or (self.holiday is True)):
            raise ValueError(
                "Non-business day must either be a weekend day or a holiday."
            )
        return self

    def merge(
        self, other: NonBusinessDaySpec | BusinessDaySpec
    ) -> Self | BusinessDaySpec:
        if not isinstance(other, NonBusinessDaySpec):
            return other  # Cannot merge business day spec with non-business day spec.
        self.weekend_day = (
            self.weekend_day if other.weekend_day is MISSING else other.weekend_day
        )
        self.holiday = self.holiday if other.holiday is MISSING else other.holiday
        return self


class BusinessDaySpec(BaseDaySpec):
    business_day: Literal[True] = True
    open: TimeLike | Literal["regular"] | MISSING = MISSING
    close: TimeLike | Literal["regular"] | MISSING = MISSING

    def merge(
        self, other: NonBusinessDaySpec | BusinessDaySpec
    ) -> Self | NonBusinessDaySpec:
        if not isinstance(other, BusinessDaySpec):
            return other  # Cannot merge business day spec with non-business day spec.
        self.open = self.open if other.open is MISSING else other.open
        self.close = self.close if other.close is MISSING else other.close
        return self


DaySpec = Annotated[
    NonBusinessDaySpec | BusinessDaySpec, Field(discriminator="business_day")
]


class Clear(BaseModel):
    type: Literal["clear"] = "clear"


CLEAR = Clear()


class DayChange(BaseModel):
    type: Literal["change"] = "change"
    spec: DaySpec | MISSING = MISSING
    name: str | None | MISSING = MISSING
    tags: set[str] | MISSING = MISSING

    def merge(self, other: DayChange) -> Self:
        self.name = self.name if other.name is MISSING else other.name
        if other.spec is not MISSING:
            self.spec = (
                other.spec if self.spec is MISSING else self.spec.merge(other.spec)
            )
        if other.tags is not MISSING:
            self.tags = other.tags if self.tags is MISSING else self.tags | other.tags
        return self


DayAction = Annotated[DayChange | Clear, Field(discriminator="type")]


def _canonicalize(value: dict[DateLike, DayChange]) -> dict[DateLike, DayChange]:
    return OrderedDict(sorted(value.items(), key=lambda t: t[0]))


ChangeSetDelta = Annotated[
    dict[DateLike, DayChange | Clear], AfterValidator(_canonicalize)
]

ChangeSetDeltaDict = dict[str, ChangeSetDelta]

ChangeSet = Annotated[dict[DateLike, DayChange], AfterValidator(_canonicalize)]

ChangeSetDict = dict[str, ChangeSet]

ChangeModeSingle = Literal["merge", "update", "replace"]

ChangeModeMulti = Literal["merge", "update", "replace", "replace_all"]
