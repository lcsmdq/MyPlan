from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app import models, schemas
from app.database import get_db
from app.models import Event as EventModel
from app.models import EventWithLocationView
from app.schemas import EventBase, EventCreate, Event, EventUpdate, EventWithLocation

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

## EVENTOS ABM ################################################################

#🎉3. Crear un nuevo evento
@router.post("/", response_model=EventWithLocation, status_code=status.HTTP_201_CREATED)
def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo evento.
    """
    # Validar que end_time > start_time
    if event_data.end_time <= event_data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be after start_time"
        )
    
    # Crear evento en la tabla
    db_event = EventModel(**event_data.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Retornar desde la vista
    created_event = db.query(EventWithLocationView).filter(
        EventWithLocationView.id == db_event.id
    ).first()
    
    return created_event

#🎉 4. Actualizar un evento
@router.put("/{event_id}", response_model=EventUpdate)
def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar un evento existente (actualización completa).
    """
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )
    
    # Actualizar campos
    update_data = event_data.dict(exclude_unset=True)
    
    # Validar fechas si se actualizan
    if 'start_time' in update_data or 'end_time' in update_data:
        start = update_data.get('start_time', db_event.start_time)
        end = update_data.get('end_time', db_event.end_time)
        if end <= start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time"
            )
    
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    
    # Retornar desde la vista
    updated_event = db.query(EventWithLocationView).filter(
        EventWithLocationView.id == event_id
    ).first()
    
    return updated_event

#🎉 5. Eliminar un evento
@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: UUID, db: Session = Depends(get_db)):
    """
    Eliminar un evento permanentemente.
    """
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )
    
    db.delete(db_event)
    db.commit()
    
    return None


## EVENTOS CONSULTAS ########################################################################

#🎉 1. Listar todos los eventos con filtros
@router.get("/", response_model=List[EventWithLocation])
def read_events(
    location_id: Optional[int] = Query(None, description="Filtrar por ubicación"),
    date: Optional[datetime] = Query(None, description="Filtrar por fecha (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filtrar por estado (active, cancelled, past)"),
    limit: int = Query(100, le=500, description="Límite de resultados"),
    offset: int = Query(0, description="Offset para paginación"),
    db: Session = Depends(get_db)
):
    """
    Listar eventos con filtros opcionales.
    """
    query = db.query(EventWithLocationView)
    
    if location_id:
        query = query.filter(EventWithLocationView.location_id == location_id)
    
    if date:
        start_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_day = datetime(date.year, date.month, date.day, 23, 59, 59)
        query = query.filter(
            EventWithLocationView.start_time >= start_day,
            EventWithLocationView.start_time <= end_day
        )
    
    if status:
        query = query.filter(EventWithLocationView.status == status)
    
    # Ordenar por fecha de inicio
    query = query.order_by(EventWithLocationView.start_time)
    
    # Paginación
    events = query.offset(offset).limit(limit).all()
    
    return events

#🎉 2. Obtener un evento específico
@router.get("/{event_id}", response_model=EventWithLocation)
def read_event(event_id: UUID, db: Session = Depends(get_db)):
    """
    Obtener detalles de un evento específico.
    """
    event = db.query(EventWithLocationView).filter(
        EventWithLocationView.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )
    
    return event

# 14. Próximos eventos
@router.get("/upcoming/", response_model=List[EventWithLocation])
def get_upcoming_events(
    days: int = Query(30, description="Días hacia adelante", ge=1, le=365),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """
    Obtener eventos próximos (del día actual en adelante).
    """
    now = datetime.now()
    future_date = now + timedelta(days=days)
    
    events = db.query(EventWithLocationView).filter(
        EventWithLocationView.start_time >= now,
        EventWithLocationView.start_time <= future_date,
       # EventWithLocationView.status == 'active'      ###AGREGAR STATUS A LA VISTA
    ).order_by(EventWithLocationView.start_time).limit(limit).all()
    
    return events