from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app import models, schemas
from app.database import get_db
from app.models import Event as EventModel
from app.schemas import EventCreate, Event

from typing import List, Optional
from fastapi import Query
from datetime import datetime
from uuid import UUID

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

# 📌 Obtener todos los eventos
@router.get("/", response_model=list[Event])
def read_events(db: Session = Depends(get_db)):
    events = db.query(EventModel).all()
    return events

# 📌 Obtener todos los eventos (con filtros opcionales)
@router.get("/", response_model=List[Event])
def read_events(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    date: Optional[datetime] = Query(None, description="Filtrar por fecha específica (YYYY-MM-DD)"),
    location_id: Optional[int] = Query(None, description="Filtrar por ubicación"),
    db: Session = Depends(get_db)
):
    query = db.query(EventModel)

    if category:
        query = query.filter(EventModel.category == category)

    if date:
        # Filtrar por rango de día
        start_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_day = datetime(date.year, date.month, date.day, 23, 59, 59)
        query = query.filter(EventModel.start_time >= start_day, EventModel.start_time <= end_day)

    if location_id:
        query = query.filter(EventModel.location_id == location_id)

    events = query.all()
    return events

# 📌 Obtener un evento por ID
@router.get("/{event_id}", response_model=Event)
def read_event(event_id: UUID, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# 📌 Crear un nuevo evento
@router.post("/", response_model=Event)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    try:
        db_event = EventModel(**event.dict())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 📌 Actualizar un evento existente
@router.put("/{event_id}", response_model=Event)
def update_event(event_id: UUID, updated_event: EventCreate, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for key, value in updated_event.dict(exclude_unset=True).items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event

# 📌 Eliminar un evento
@router.delete("/{event_id}")
def delete_event(event_id: UUID, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()
    return {"detail": "Event deleted"}
