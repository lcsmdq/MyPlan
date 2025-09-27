from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID



# Esquema base para eventos
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    is_recurring: Optional[bool] = False
    recurrence_rule: Optional[str] = None
    created_by: Optional[UUID] = None
    status: Optional[str] = "active"
    
    
 

class Config:
    from_attributes = True  # Reemplaza orm_mode=True en Pydantic v2

# Esquema para crear un nuevo evento
class EventCreate(EventBase):
    pass  # Hereda todos los campos de EventBase

# Esquema de respuesta (incluye ID)
class Event(EventBase):
    id: UUID
    created_at: datetime