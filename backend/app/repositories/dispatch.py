"""Control-room messages and route plans, kept in memory (demo) or in SQL (MySQL)."""

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import MessageRecord, RoutePlanRecord


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # stored as naive UTC


def _message(record: MessageRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "driver_id": record.driver_id,
        "text": record.text,
        "pref": record.pref,
        "created_at": record.created_at.replace(tzinfo=timezone.utc),
        "read": record.read,
    }


class DispatchStore:
    """Demo mode keeps everything in this process, so it is lost when the server restarts."""

    def __init__(self, sessions: sessionmaker[Session] | None = None) -> None:
        self._sessions = sessions
        self._lock = Lock()
        self._messages: list[dict[str, Any]] = []
        self._plans: dict[str, str] = {}

    def snapshot(self, driver_id: str | None = None) -> dict[str, Any]:
        if self._sessions is None:
            with self._lock:
                messages = [m.copy() for m in self._messages if driver_id in (None, m["driver_id"])]
                plans = {k: v for k, v in self._plans.items() if driver_id in (None, k)}
        else:
            with self._sessions() as session:
                query = select(MessageRecord)
                plan_query = select(RoutePlanRecord)
                if driver_id is not None:
                    query = query.where(MessageRecord.driver_id == driver_id)
                    plan_query = plan_query.where(RoutePlanRecord.driver_id == driver_id)
                messages = [_message(m) for m in session.scalars(query)]
                plans = {p.driver_id: p.pref for p in session.scalars(plan_query)}
        messages.sort(key=lambda m: m["id"], reverse=True)
        return {"messages": messages, "plans": plans}

    def add_message(self, driver_id: str, text: str | None = None, pref: str | None = None) -> dict[str, Any]:
        if self._sessions is None:
            with self._lock:
                message = {
                    "id": len(self._messages) + 1,
                    "driver_id": driver_id,
                    "text": text,
                    "pref": pref,
                    "created_at": datetime.now(timezone.utc),
                    "read": False,
                }
                self._messages.append(message)
                return message.copy()
        with self._sessions.begin() as session:
            record = MessageRecord(driver_id=driver_id, text=text, pref=pref, created_at=_now(), read=False)
            session.add(record)
            session.flush()
            return _message(record)

    def mark_read(self, driver_id: str) -> None:
        if self._sessions is None:
            with self._lock:
                for message in self._messages:
                    if message["driver_id"] == driver_id:
                        message["read"] = True
            return
        with self._sessions.begin() as session:
            session.execute(update(MessageRecord).where(MessageRecord.driver_id == driver_id).values(read=True))

    def set_plan(self, driver_id: str, pref: str) -> dict[str, Any]:
        """Assign a route option and tell the driver about it in a message."""
        if self._sessions is None:
            with self._lock:
                self._plans[driver_id] = pref
        else:
            with self._sessions.begin() as session:
                record = session.get(RoutePlanRecord, driver_id)
                if record is None:
                    session.add(RoutePlanRecord(driver_id=driver_id, pref=pref, updated_at=_now()))
                else:
                    record.pref, record.updated_at = pref, _now()
        return self.add_message(driver_id, pref=pref)
