from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer

from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPublicProfile,
    LoginRequest,
    AuthResponse,
    ChangePasswordRequest
)

from app.crud import users as crud_users

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Agregar al inicio del archivo después de los imports
security = HTTPBearer(auto_error=True)

from app.crud import users as crud_users
from app.config import settings

router = APIRouter(tags=["Authentication & Users"])


# ==================== JWT HELPERS ====================

def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT token con el user_id."""
    to_encode = {"sub": str(user_id)}
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> UUID:
    """Verifica y decodifica el JWT token, devuelve el user_id."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        return UUID(user_id)
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency para obtener el usuario autenticado desde el token JWT."""
    
    token = credentials.credentials
    
    # 🔍 DEBUG - Temporal
    print(f"=== DEBUG AUTH ===")
    print(f"Token recibido: {token}")
    
    user_id = verify_token(token)
    user = crud_users.get_user(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    return user


# ==================== AUTH ENDPOINTS ====================

@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registrar un nuevo usuario.
    
    - Valida que el email no exista
    - Valida que el nombre no exista
    - Hashea la contraseña
    - Devuelve token JWT
    """
    # Verificar si el email ya existe
    if crud_users.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Verificar si el nombre ya existe
    if crud_users.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre ya está en uso"
        )
    
    # Crear usuario
    user = crud_users.create_user(db, user_data)
    
    # Generar token JWT
    access_token = create_access_token(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/auth/login", response_model=AuthResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login con email/username y contraseña.
    
    - Acepta email o username como identificador
    - Verifica la contraseña
    - Devuelve token JWT
    """
    user = crud_users.authenticate_user(db, login_data.identifier, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar token JWT
    access_token = create_access_token(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/auth/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambiar contraseña del usuario autenticado.
    
    - Requiere contraseña actual
    - Valida nueva contraseña
    """
    success = crud_users.change_password(
        db, 
        current_user.id, 
        password_data.old_password, 
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    return {"message": "Contraseña actualizada exitosamente"}


# ==================== USER ENDPOINTS ====================
#devolver datos del perfil del usuario
@router.get("/users/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Obtener mi perfil (usuario autenticado)."""
    return current_user


@router.patch("/users/me", response_model=UserResponse)
def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Campos editables:
    - profile_picture
    - role
    - creator_type
    - bio
    """
    updated_user = crud_users.update_user(db, current_user.id, user_update)
    return updated_user


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar mi cuenta.
    
    CUIDADO: Esta acción es irreversible.
    """
    crud_users.delete_user(db, current_user.id)
    return None


@router.get("/users/{user_id}", response_model=UserPublicProfile)
def get_user_public_profile(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Obtener perfil público de otro usuario."""
    user = crud_users.get_user(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return user

#Listar usuarios (perfiles públicos)
'''
@router.get("/users", response_model=List[UserPublicProfile])
def list_users(
    skip: int = 0,
    limit: int = 100,
    #is_event_creator: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Listar usuarios (perfiles públicos).
    
    Filtros opcionales:
    - is_event_creator: filtrar por creadores de eventos
    """
    users = crud_users.get_users(db, skip=skip, limit=limit)
    return users

'''