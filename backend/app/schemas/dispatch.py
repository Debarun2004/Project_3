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


class DeliveryCreate(BaseModel):
    """A parcel handed over: the route option driven and the CO₂ that parcel's share of the trip saved."""

    model_config = ConfigDict(extra="forbid")

    pref: RoutePreference = "fastest"
    co2_saved_kg: float = Field(default=0, ge=0, le=1000)


class Delivery(BaseModel):
    id: int
    trip_id: str
    driver_id: str
    parcel: int
    pref: RoutePreference
    co2_saved_kg: float
    created_at: datetime


class Dispatch(BaseModel):
    """Messages and deliveries (newest first) and each driver's assigned route option."""

    messages: list[Message]
    plans: dict[str, RoutePreference]
    deliveries: list[Delivery] = []
