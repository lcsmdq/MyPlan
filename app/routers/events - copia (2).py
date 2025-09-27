from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app import schemas
from app import database
from app.database import SessionLocal, get_db
from app.models import Event as EventModel   # Modelo SQLAlchemy (BD)
from app.schemas import EventCreate, Event   # Schemas Pydantic (validación)


router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

#Lee todos los eventos
@router.get("/")
def read_events():
    db = SessionLocal()
    try:
        # Debug: Ver que la sesión se crea
        print("Sesión DB creada")

        # Intentamos hacer la consulta
        events = db.query(models.Event).all()
        print(f"Eventos encontrados: {events}")

        return events

    except Exception as e:
        # Mostramos el error completo en consola
        print(f"Error en DB: {e}")
        raise HTTPException(status_code=500, detail=f"Error en DB: {e}")

    finally:
        db.close()
        print("Sesión DB cerrada")

# Crear evento
@router.post("/", response_model=Event)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    try:
        new_event = EventModel(**event.dict())  # ✅ Convertimos Pydantic a SQLAlchemy
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en DB: {e}")

#@router.post("/", response_model=schemas.Event)
#def create_event(event: schemas.EventCreate, db: Session = Depends(database.get_db)):
#    new_event = models.Event(**event.dict())  # 👈 aquí usamos models, no schemas
#    db.add(new_event)
#    db.commit()
#    db.refresh(new_event)
#    return new_event


