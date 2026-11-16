"""Schemas for control-room messages and assigned route options."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RoutePreference = Literal["fastest", "balanced", "greenest"]


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    driver_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=1000)


class Message(BaseModel):
    id: int
    driver_id: str
    text: str | None = None
    pref: RoutePreference | None = None
    created_at: datetime
    read: bool = False


class MarkRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    driver_id: str = Field(min_length=1, max_length=64)


class PlanSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    driver_id: str = Field(min_length=1, max_length=64)
    pref: RoutePreference


class Dispatch(BaseModel):
    """Messages (newest first) and each driver's assigned route option."""

    messages: list[Message]
    plans: dict[str, RoutePreference]
