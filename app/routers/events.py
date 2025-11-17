from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app import models, schemas
from app.database import get_db
from app.models import Event as EventModel
from app.models import EventWithLocationView
from app.schemas import EventBase, EventCreate, Event, EventUpdate, EventWithLocation
from app.schemas import (
    AssistCreate, 
    AssistResponse, 
    AssistWithEvent, 
    EventAssistStats,
    AssistStatus
)

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.models import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/events", tags=["Events"])


## EVENTOS ABM ################################################################

#🎉 3. Crear un nuevo evento
@router.post("/", response_model=EventWithLocation, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    """
    Crear un nuevo evento.
    Requiere autenticación y el rol de 'organizer'.
    """
  
    # 1. 🛑 VERIFICACIÓN DE ROL 
    # Asegúrate de que 'role' sea el nombre del campo y 'organizer' el valor correcto
    if current_user.role != "organizer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must have 'organizer' role to create an event"
        )
    
    # 2. Validar que end_time > start_time
    if event_data.end_time <= event_data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be after start_time"
        )
    
    # 3. Preparar los datos del evento, incluyendo el ID del creador
    event_data_dict = event_data.dict()
    # Usaremos 'created_by' para coincidir con el campo de tu tabla
    event_data_dict['created_by'] = current_user.id 
    
    # 4. Crear evento en la tabla
    db_event = EventModel(**event_data_dict) 
    
    db.add(db_event)
    
    try:
        db.commit()
        db.refresh(db_event)
    except Exception as e:
        db.rollback()
        # Si la Foreign Key todavía está mal, fallará aquí, pero con el cambio 
        # anterior a 'created_by' y la corrección de la FK, debería funcionar.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during event creation: {str(e)}"
        )
    
    # 5. Retornar desde la vista
    created_event = db.query(EventWithLocationView).filter(
        EventWithLocationView.id == db_event.id
    ).first()
    
    return created_event

#🎉 4. Actualizar un evento
@router.put("/{event_id}", response_model=EventUpdate)
def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
def delete_event(
    event_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
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

#🎉 2. Obtener un evento específico
@router.get("/{event_id}", response_model=EventWithLocation)
def read_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
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
# 🎉 2. Obtener todos los eventos creados por el usuario autenticado
@router.get("/by_created_by/", response_model=List[EventWithLocation])
def get_my_created_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500)
):
    """
    Obtener todos los eventos creados por el usuario autenticado.
    
    - Retorna lista ordenada por fecha de creación (más recientes primero)
    - Soporta paginación con skip y limit
    """
    events = db.query(EventWithLocationView).filter(
        EventWithLocationView.created_by == current_user.id
    ).order_by(
        EventWithLocationView.created_at.desc()  # Más recientes primero
    ).offset(skip).limit(limit).all()
    
    if not events:
        # Retornar lista vacía en lugar de error
        return []
    
    return events

# 9. Filtrar por rango de fechas, locacion y categoria
@router.get("/by-date-range/", response_model=List[EventWithLocation])
def get_events_by_date_range(
    start_date: datetime = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    location_id: Optional[int] = Query(None, description="Filtrar por ID de ubicación"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener eventos dentro de un rango de fechas.
    
    Busca eventos cuya fecha de inicio esté entre start_date y end_date (inclusive).
    """
    # Validar rango
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be greater than or equal to start_date"
        )
    
    # Validar que el rango no sea muy grande (opcional)
    date_diff = (end_date - start_date).days
    if date_diff > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 365 days"
        )
    
    # Query base
    query = db.query(EventWithLocationView)
    
    # Filtrar por rango de fechas
    end_of_day = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    query = query.filter(
        EventWithLocationView.start_time >= start_date,
        EventWithLocationView.start_time <= end_of_day
    )
    
    # Filtros adicionales
    # Aplicar filtro por location_id si se proporciona
    if location_id is not None:
        query = query.filter(EventWithLocationView.location_id == location_id)
    
    # Aplicar filtro por categoría si se proporciona
    if category is not None:
        query = query.filter(EventWithLocationView.category == category)
 
    
    # Ordenar y paginar
    events = query.order_by(EventWithLocationView.start_time)\
                  .offset(offset)\
                  .limit(limit)\
                  .all()
    
    return events