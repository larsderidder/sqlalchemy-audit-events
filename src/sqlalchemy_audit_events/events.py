from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable
from uuid import uuid4

import pytz
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import bind_contextvars


class AccountabilityMixin:
    """Marker mixin for models that track who last updated them."""

    updated_by_user_id: int | None
    updated_by_service_id: int | None


class CreatedAndUpdatedMixin:
    """Marker mixin for models that track a last-updated timestamp."""

    was_last_updated_on: datetime | None


def default_transaction_id() -> str:
    """Generate a default transaction ID."""
    return f"txn-{uuid4().hex}"


@dataclass
class SessionInfo:
    """Holds session-scoped context used by event hooks."""

    user_id: int | None = None
    service_user_id: int | None = None
    transaction_id: str = field(default_factory=default_transaction_id)
    bind_context: Callable[..., None] = bind_contextvars

    def update_logging_context(self) -> None:
        """Bind session context into structlog contextvars."""
        self.bind_context(
            user_id=self.user_id,
            service_user_id=self.service_user_id,
            transaction_id=self.transaction_id,
        )


def ensure_session_info(session: AsyncSession) -> SessionInfo:
    """Ensure SessionInfo is present on the SQLAlchemy session."""
    if "session_info" not in session.info:
        session.info["session_info"] = SessionInfo()
    return session.info["session_info"]


def register_session_events(
    session: AsyncSession,
    accountability_types: tuple[type, ...] = (AccountabilityMixin,),
    timestamp_types: tuple[type, ...] = (CreatedAndUpdatedMixin,),
) -> None:
    """Register session events for audit field updates."""
    ensure_session_info(session)

    @event.listens_for(session.sync_session, "before_flush")
    def update_was_last_updated_by_on_flush(_sess, _flush_context, _instances):
        dirties = [dirty for dirty in session.dirty if isinstance(dirty, accountability_types)]
        dirties += [dirty for dirty in session.new if isinstance(dirty, accountability_types)]
        info: SessionInfo = session.info["session_info"]
        user_id = info.user_id
        service_user_id = info.service_user_id
        for dirty in dirties:
            if user_id is not None:
                dirty.updated_by_user_id = user_id
            if service_user_id is not None:
                dirty.updated_by_service_id = service_user_id

    @event.listens_for(session.sync_session, "before_flush")
    def update_was_last_updated_on_flush(_sess, _flush_context, _instances):
        dirties = [dirty for dirty in session.dirty if isinstance(dirty, timestamp_types)]
        dirties += [dirty for dirty in session.new if isinstance(dirty, timestamp_types)]
        for dirty in dirties:
            dirty.was_last_updated_on = datetime.now(tz=pytz.UTC)


def register_user_in_session_info(session: AsyncSession, user_id: int) -> None:
    """Register a user in session info."""
    info = ensure_session_info(session)
    info.user_id = user_id
    info.update_logging_context()
