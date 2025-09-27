
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.models import Event as EventModel
from app.schemas import EventCreate, Event

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
        events = db.query(Event).all()
        print(f"Eventos encontrados: {events}")

        return events

    except Exception as e:
        # Mostramos el error completo en consola
        print(f"Error en DB: {e}")
        raise HTTPException(status_code=500, detail=f"Error en DB: {e}")

    finally:
        db.close()
        print("Sesión DB cerrada")

