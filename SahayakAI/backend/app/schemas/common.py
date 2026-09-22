"""
Common Schema Mixins and Base Types.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TimestampSchema(BaseModel):
    """Timestamp metadata mixin for read schemas."""

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
