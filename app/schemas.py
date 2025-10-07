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

class EventWithLocation(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    location_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    location_name: Optional[str] = None  # ✅ Del JOIN 
 

class Config:
    from_attributes = True  # Reemplaza orm_mode=True en Pydantic v2

# Esquema para crear un nuevo evento
class EventCreate(EventBase):
    pass  # Hereda todos los campos de EventBase

# Esquema de respuesta (incluye ID)
class Event(EventBase):
    id: UUID
    created_at: Optional[datetime] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    status: Optional[str] = None

# ✅ Schema para respuestas (incluye location_name de la vista)
class Event(EventBase):
    id: UUID
    created_at: Optional[datetime] = None
    location_name: Optional[str] = None  # ✅ Campo de la vista
    
    class Config:
        from_attributes = True  # Para FastAPI 0.100+
        # orm_mode = True  # Si usas versión anterior

# Schema sin location_name para operaciones que no usan la vista
class EventSimple(EventBase):
    id: UUID
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True