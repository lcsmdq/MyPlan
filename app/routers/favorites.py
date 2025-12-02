from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import User
from app.schemas import (
    FavoriteCreate,
    FavoriteResponse,
    FavoriteCategoryList
)

from app.routers.auth import get_current_user
from app.crud import favorites as crud_favorites


router = APIRouter(prefix="/favorites", tags=["Favorites"])


# ==================== FAVORITES ENDPOINTS ====================

@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite_category(
    favorite: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Agregar una categoría a favoritos del usuario autenticado.
    
    - Si ya existe, retorna error 409 (Conflict)
    """
    db_favorite = crud_favorites.create_favorite(db, current_user.id, favorite)
    
    if not db_favorite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta categoría ya está en tus favoritos"
        )
    
    return db_favorite


@router.get("/", response_model=List[FavoriteResponse])
def get_my_favorite_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las categorías favoritas del usuario autenticado.
    
    Retorna lista completa con IDs y timestamps.
    """
    favorites = crud_favorites.get_user_favorites(db, current_user.id)
    return {"favorites": favorites}


@router.get("/ids", response_model=FavoriteCategoryList)
def get_my_favorite_category_ids(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener solo los IDs de categorías favoritas del usuario.
    
    Útil para checkear rápidamente si una categoría es favorita.
    """
    category_ids = crud_favorites.get_user_favorite_ids(db, current_user.id)
    return {"category_ids": category_ids}


@router.get("/check/{category_id}", response_model=dict)
def check_if_favorite(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verificar si una categoría específica es favorita del usuario.
    
    Retorna: {"is_favorite": true/false}
    """
    is_fav = crud_favorites.is_favorite(db, current_user.id, category_id)
    return {"is_favorite": is_fav}


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar una categoría de favoritos (soft delete).
    
    - Marca como eliminado pero mantiene el registro histórico
    - Retorna 204 si se eliminó
    - Retorna 404 si no existía
    """
    deleted = crud_favorites.delete_favorite(db, current_user.id, category_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esta categoría no está en tus favoritos"
        )
    
    return None




@router.get("/count", response_model=dict)
def count_my_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Contar cuántas categorías favoritas tiene el usuario.
    
    Retorna: {"count": number}
    """
    count = crud_favorites.count_user_favorites(db, current_user.id)
    return {"count": count}


# ==================== ADMIN ENDPOINTS (opcional) ====================

@router.get("/users/{user_id}", response_model=List[FavoriteResponse])
def get_user_favorites_admin(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    [ADMIN] Obtener favoritos de cualquier usuario.
    
    Requiere rol de admin (implementar validación de rol si es necesario).
    """
    # TODO: Validar que current_user.role == 'admin'
    # if current_user.role != 'admin':
    #     raise HTTPException(status_code=403, detail="No autorizado")
    
    favorites = crud_favorites.get_user_favorites(db, user_id)
    return favorites


