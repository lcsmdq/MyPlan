from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID
from passlib.context import CryptContext
import bcrypt

from app.models import User
from app.schemas import UserCreate, UserUpdate

# Configuración para hashear contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """Obtener usuario por ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Obtener usuario por email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Obtener usuario por username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email_or_username(db: Session, identifier: str) -> Optional[User]:
    """Obtener usuario por email o username"""
    return db.query(User).filter(
        or_(User.email == identifier, User.username == identifier)
    ).first()


def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    role: Optional[str] = None,
    creator_type: Optional[str] = None
) -> List[User]:
    """Obtener lista de usuarios con paginación"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if creator_type:
        query = query.filter(User.creator_type == creator_type)
    
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Crear nuevo usuario"""
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        name=user.username
        #profile_picture=getattr(user, 'profile_picture', None),
        #is_event_creator=user.is_event_creator or False,
        #event_category=user.event_category
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_user(db: Session, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
    """
    Actualizar usuario.
    Solo permite actualizar: profile_picture

     Si en el futuro quieres permitir más campos:
     Solo agrega el campo a allowed_fields:
     allowed_fields = {'profile_picture', 'bio'}  # Ejemplo

    """
    db_user = get_user(db, user_id)
    
    if not db_user:
        return None
    
    # Obtener datos a actualizar (solo los que se enviaron)
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Lista blanca de campos permitidos para actualizar
    allowed_fields = {'profile_picture', 'role','creator_type','bio'}
    
    # Filtrar solo campos permitidos
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user


def delete_user(db: Session, user_id: UUID) -> bool:
    """Eliminar usuario"""
    db_user = get_user(db, user_id)
    
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    
    return True


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """
    Autenticar usuario con email/username y contraseña.
    Devuelve el usuario si las credenciales son correctas, None si no.
    """
    user = get_user_by_email_or_username(db, identifier)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def change_password(db: Session, user_id: UUID, old_password: str, new_password: str) -> bool:
    """Cambiar contraseña del usuario"""
    user = get_user(db, user_id)
    
    if not user:
        return False
    
    # Verificar contraseña actual
    if not verify_password(old_password, user.hashed_password):
        return False
    
    # Actualizar con nueva contraseña
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return True