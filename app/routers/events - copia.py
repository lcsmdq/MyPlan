from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app import schemas
from app import database
from app.database import SessionLocal, get_db
from app.models import Event as EventModel   # Modelo SQLAlchemy (BD)
from app.schemas import EventCreate, Event   # Schemas Pydantic (validación)
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