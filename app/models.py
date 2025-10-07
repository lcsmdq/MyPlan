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

class EventWithLocationView(Base):
    __tablename__ = "events_with_location"
    __table_args__ = {'schema': 'public'}
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    location_id = Column(Integer)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location_name = Column(String)  # ✅ Campo extra de la vista
    def __repr__(self):
        return f"<EventWithLocation(id={self.id}, location_id={self.location_id}, title={self.title})>"