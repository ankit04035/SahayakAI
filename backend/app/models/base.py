"""
Base Model and Mixin Definitions.
Provides UTC timezone-aware timestamping helpers and base model utilities.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, TypeDecorator


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """
    Timezone-aware UTC DateTime type for cross-dialect compatibility (especially SQLite).
    Ensures timestamps are always stored in UTC and return with tzinfo=timezone.utc.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
        return value


class TimestampMixin:
    """Reusable mixin providing timezone-aware created_at and updated_at columns."""

    created_at = Column(
        UTCDateTime,
        default=utc_now,
        nullable=False,
    )
    updated_at = Column(
        UTCDateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
