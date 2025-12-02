from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models import Favorite
from app.schemas import FavoriteCreate


def get_favorite(db: Session, favorite_id: int, include_deleted: bool = False) -> Optional[Favorite]:
    """Obtener un favorito por ID"""
    query = db.query(Favorite).filter(Favorite.id == favorite_id)
    
    if not include_deleted:
        query = query.filter(Favorite.deleted_at.is_(None))
    
    return query.first()


def get_user_favorite(db: Session, user_id: UUID, category_id: int) -> Optional[Favorite]:
    """Obtener favorito específico de un usuario (solo activos)"""
    return db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.category_id == category_id,
        Favorite.deleted_at.is_(None)
    ).first()


def get_user_favorites(db: Session, user_id: UUID, include_deleted: bool = False) -> List[Favorite]:
    """Obtener todas las categorías favoritas de un usuario"""
    query = db.query(Favorite).filter(Favorite.user_id == user_id)
    
    if not include_deleted:
        query = query.filter(Favorite.deleted_at.is_(None))
    
    return query.order_by(Favorite.created_at.desc()).all()


def get_user_favorite_ids(db: Session, user_id: UUID) -> List[int]:
    """Obtener solo los IDs de categorías favoritas activas de un usuario"""
    favorites = db.query(Favorite.category_id).filter(
        Favorite.user_id == user_id,
        Favorite.deleted_at.is_(None)
    ).all()
    return [fav.category_id for fav in favorites]


def create_favorite(db: Session, user_id: UUID, favorite: FavoriteCreate) -> Optional[Favorite]:
    """
    Agregar una categoría a favoritos.
    Si existía previamente pero fue eliminado (soft delete), lo reactiva.
    Retorna None si ya existe activo.
    """
    # Verificar si existe (activo o eliminado)
    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.category_id == favorite.category_id
    ).first()
    
    if existing:
        if existing.deleted_at is None:
            # Ya existe y está activo
            return None
        else:
            # Existía pero estaba eliminado, reactivarlo
            existing.deleted_at = None
            db.commit()
            db.refresh(existing)
            return existing
    
    # Crear nuevo favorito
    db_favorite = Favorite(
        user_id=user_id,
        category_id=favorite.category_id
    )
    
    try:
        db.add(db_favorite)
        db.commit()
        db.refresh(db_favorite)
        return db_favorite
    except IntegrityError:
        db.rollback()
        return None


def delete_favorite(db: Session, user_id: UUID, category_id: int) -> bool:
    """
    Soft delete: marca una categoría como eliminada en lugar de borrarla.
    Retorna True si se eliminó, False si no existía.
    """
    favorite = get_user_favorite(db, user_id, category_id)
    
    if not favorite:
        return False
    
    # Soft delete: marcar como eliminado
    favorite.deleted_at = datetime.now()
    db.commit()
    return True


def delete_favorite_by_id(db: Session, user_id: UUID, favorite_id: int) -> bool:
    """
    Soft delete por ID.
    Solo permite eliminar favoritos del propio usuario.
    """
    favorite = db.query(Favorite).filter(
        Favorite.id == favorite_id,
        Favorite.user_id == user_id,
        Favorite.deleted_at.is_(None)
    ).first()
    
    if not favorite:
        return False
    
    # Soft delete
    favorite.deleted_at = datetime.now()
    db.commit()
    return True


def restore_favorite(db: Session, user_id: UUID, category_id: int) -> Optional[Favorite]:
    """
    Restaurar un favorito eliminado (reactivarlo).
    """
    favorite = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.category_id == category_id,
        Favorite.deleted_at.isnot(None)
    ).first()
    
    if not favorite:
        return None
    
    favorite.deleted_at = None
    db.commit()
    db.refresh(favorite)
    return favorite


def is_favorite(db: Session, user_id: UUID, category_id: int) -> bool:
    """Verificar si una categoría es favorita activa del usuario"""
    return get_user_favorite(db, user_id, category_id) is not None


def count_user_favorites(db: Session, user_id: UUID, include_deleted: bool = False) -> int:
    """Contar cuántas categorías favoritas tiene un usuario"""
    query = db.query(Favorite).filter(Favorite.user_id == user_id)
    
    if not include_deleted:
        query = query.filter(Favorite.deleted_at.is_(None))
    
    return query.count()


def get_favorite_history(db: Session, user_id: UUID) -> List[Favorite]:
    """
    Obtener historial completo de favoritos del usuario.
    Incluye activos y eliminados, útil para análisis.
    """
    return db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).order_by(Favorite.created_at.desc()).all()