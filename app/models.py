import uuid
from sqlalchemy import UUID, Boolean, Column, Integer, String, DateTime, Text
from .database import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text)
    location_id = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    status = Column(Text, default='active')
    created_at = Column(DateTime)