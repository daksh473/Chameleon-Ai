from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import DeclarativeBase

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
