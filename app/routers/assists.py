from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID


from app.models import Assist, EventWithLocationView, User
from app.schemas import (
    AssistCreate, 
    AssistResponse, 
    AssistWithEvent, 
    EventAssistStats,
    AssistStatus
)

from app.routers.auth import get_current_user
from app.database import get_db
# from app.dependencies import get_current_user  # Para obtener el user_id autenticado

router = APIRouter(prefix="/assists", tags=["assists"])


# ==================== GESTIÓN DE ASISTENCIAS/LIKES ====================

# 30. Marcar evento (assist o like)
# --- Endpoint para Marcar/Desmarcar 'Assist' ---
@router.post("/{event_id}/assist", response_model=AssistResponse, status_code=status.HTTP_200_OK)
def toggle_assist(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    """
    Marcar o desmarcar un evento como 'assist' (asistiré).
    Si ya existe la marca, la elimina (desmarca).
    """
    event = db.query(EventWithLocationView).filter(
        EventWithLocationView.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    # Intenta encontrar la marca 'assist' existente
    existing_mark = db.query(Assist).filter(
        Assist.user_id == current_user.id,
        Assist.event_id == event_id,
        Assist.status == AssistStatus.ASSIST.value # Asumiendo que AssistStatus es un Enum
    ).first()
    
    if existing_mark:
        # Ya existe -> Desmarcar (Eliminar)
        db.delete(existing_mark)
        db.commit()
        # Retorna una respuesta adecuada para 'desmarcado' (puede ser un DTO especial o el mismo objeto si lo ajustas)
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT, # No Content es común para DELETE exitoso
            detail="Assist mark removed successfully"
        )
    
    # No existe -> Marcar (Crear)
    new_assist = Assist(
        user_id=current_user.id,
        event_id=event_id,
        status=AssistStatus.ASSIST.value
    )
    
    db.add(new_assist)
    db.commit()
    db.refresh(new_assist)
    
    return new_assist

# --- Endpoint para Marcar/Desmarcar 'Like' ---
@router.post("/{event_id}/like", response_model=AssistResponse, status_code=status.HTTP_200_OK)
def toggle_like(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )   
    """
    Marcar o desmarcar un evento como 'like' (me gusta).
    Si ya existe la marca, la elimina (desmarca).
    """
    event = db.query(EventWithLocationView).filter(
        EventWithLocationView.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    # Intenta encontrar la marca 'like' existente
    existing_mark = db.query(Assist).filter(
        Assist.user_id == current_user.id,
        Assist.event_id == event_id,
        Assist.status == AssistStatus.LIKE.value
    ).first()
    
    if existing_mark:
        # Ya existe -> Desmarcar (Eliminar)
        db.delete(existing_mark)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Like mark removed successfully"
        )

    # No existe -> Marcar (Crear)
    new_assist = Assist(
        user_id=current_user.id,
        event_id=event_id,
        status=AssistStatus.LIKE.value
    )
    
    db.add(new_assist)
    db.commit()
    db.refresh(new_assist)
    
    return new_assist


# 33. Obtener estadísticas de un evento (cuántos assists/likes tiene)
@router.get("/{event_id}/stats", response_model=EventAssistStats)
def get_event_stats(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de asistencias y likes de un evento.
    """
    # Verificar que el evento existe
    event = db.query(EventWithLocationView).filter(
        EventWithLocationView.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    # Contar assists
    total_assists = db.query(func.count(Assist.id)).filter(
        Assist.event_id == event_id,
        Assist.status == 'assist'
    ).scalar() or 0
    
    # Contar likes
    total_likes = db.query(func.count(Assist.id)).filter(
        Assist.event_id == event_id,
        Assist.status == 'like'
    ).scalar() or 0
    
    return {
        "event_id": event_id,
        "total_assists": total_assists,
        "total_likes": total_likes,
        "total": total_assists + total_likes
    }


# BONUS: Verificar marcas LIKE ASSIST del usuario logueado. si no se pasa event_id trae todo
@router.get("/my-marks", response_model=List[AssistResponse])
def get_my_marks_for_event_or_all(
    # event_id ahora es un query parameter y es opcional
    event_id: Optional[UUID] = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verificar qué marcas tiene el usuario actual en un evento específico (o en todos los eventos).
    
    - Si se pasa 'event_id', retorna las marcas del usuario para ese evento.
    - Si 'event_id' es None, retorna todas las marcas del usuario en todos los eventos.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # 1. Iniciar la consulta
    query = db.query(Assist).filter(
        Assist.user_id == current_user.id
    )
    
    # 2. Aplicar el filtro de event_id si se proporciona
    if event_id:
        query = query.filter(
            Assist.event_id == event_id
        )
    
    # 3. Ejecutar la consulta
    marks = query.all()
    
    return marks

# 32. Ver eventos marcados por el usuario (mis asistencias/likes)
'''
@router.get("/marked", response_model=List[AssistWithEvent])
def get_my_marked_events(
    status_type: Optional[AssistStatus] = Query(None, description="Filtrar por tipo de marcado"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener todos los eventos marcados por el usuario actual.
    
    - Sin filtro: devuelve tanto 'assist' como 'like'
    - Con filtro: devuelve solo el tipo especificado
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    query = db.query(Assist).filter(Assist.user_id == current_user)
    
    if status_type:
        query = query.filter(Assist.status == status_type.value)
    
    assists = query.order_by(Assist.created_at.desc()).all()
    
    # Enriquecer con información del evento
    result = []
    for assist in assists:
        event = db.query(EventWithLocationView).filter(
            EventWithLocationView.id == assist.event_id
        ).first()
        
        result.append({
            "id": assist.id,
            "user_id": assist.user_id,
            "event_id": assist.event_id,
            "status": assist.status,
            "created_at": assist.created_at,
            "event": event
        })
    
    return result
'''