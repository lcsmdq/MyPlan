from pydantic import BaseModel, field_validator, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
import re

from enum import Enum
from pydantic import BaseModel, field_validator, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum
import re



# Esquema base para eventos
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    is_recurring: Optional[bool] = False
    # recurrence_rule: Optional[str] = None
    created_by: Optional[UUID] = None
    status: Optional[str] = "active"
    created_at: datetime = None
    # category: Optional[int]  = None
    edited_at: Optional[datetime] = None

class EventWithLocation(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    location_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    # category: Optional[int] = None
    location_name: Optional[str] = None  # ✅ Del JOIN 
 

class Config:
    from_attributes = True  # Reemplaza orm_mode=True en Pydantic v2

# Esquema para crear un nuevo evento
class EventCreate(EventBase):
    pass  # Hereda todos los campos de EventBase

# Esquema de respuesta (incluye ID)
class Event(EventBase):
    id: UUID
    created_at: Optional[datetime] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    #recurrence_rule: Optional[str] = None
    status: Optional[str] = None
    #category: Optional[int]  = None
    edited_at: Optional[datetime] = None

# ✅ Schema para respuestas (incluye location_name de la vista)
class Event(EventBase):
    id: UUID
    created_at: Optional[datetime] = None
    location_name: Optional[str] = None  # ✅ Campo de la vista
    
    class Config:
        from_attributes = True  # Para FastAPI 0.100+
        # orm_mode = True  # Si usas versión anterior

# Schema sin location_name para operaciones que no usan la vista
class EventSimple(EventBase):
    id: UUID
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        

####               ESTADO                #################################################
# Enum para el estado
class AssistStatus(str, Enum):
    ASSIST = "assist"
    LIKE = "like"
     


# Schema para crear/actualizar
class AssistCreate(BaseModel):
    event_id: UUID
    status: AssistStatus


# Schema para respuesta
class AssistResponse(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    status: AssistStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


# Schema para respuesta con información del evento
class AssistWithEvent(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    status: AssistStatus
    created_at: datetime
    event: Optional[EventWithLocation] = None  # Información del evento
    
    class Config:
        from_attributes = True


# Schema para estadísticas de un evento
class EventAssistStats(BaseModel):
    event_id: UUID
    total_assists: int
    total_likes: int
    total: int


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    """Base de usuario con campos comunes"""
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)
    role: Literal['user', 'organizer', 'admin'] = 'user'
    creator_type: Optional[Literal['comercio', 'planner', 'fundraiser','null']] = 'null'
    
    @field_validator('creator_type')
    @classmethod
    def validate_creator_type(cls, v, info):
        # Solo los organizadores pueden tener creator_type
        role = info.data.get('role')
        if v is not None and role != 'organizer':
            raise ValueError('creator_type solo puede establecerse si role es "organizer"')
        return v


class UserCreate(UserBase):
    """Schema para crear usuario"""
    username: str
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Debe tener al menos una letra y un número
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


class UserUpdate(BaseModel):
    """
    Schema para actualizar perfil de usuario.
    
    Campos editables:
    - profile_picture
    - role
    - creator_type
    - bio
    """
    profile_picture: Optional[str] = Field(None, description="URL de la imagen de perfil")
    role: str
    creator_type : str
    bio: Optional[str]

    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Respuesta con datos del usuario (sin contraseña)"""
    id: UUID
    email: str
    username: str
    role: str
    creator_type: Optional[str]
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserPublicProfile(BaseModel):
    """Perfil público del usuario (información limitada)"""
    id: UUID
    username: str
    role: str
    creator_type: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== AUTH SCHEMAS ====================

class LoginRequest(BaseModel):
    """Request de login"""
    identifier: str = Field(..., description="Email o nombre de usuario")
    password: str


class AuthResponse(BaseModel):
    """Respuesta de autenticación exitosa"""
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    """Request para cambiar contraseña"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


class TokenData(BaseModel):
    """Datos contenidos en el JWT token"""
    user_id: Optional[UUID] = None

# ==================== FAVORITE SCHEMAS ====================

class FavoriteCreate(BaseModel):
    """Schema para agregar una categoría favorita"""
    category_id: int


class FavoriteResponse(BaseModel):
    """Respuesta con información del favorito"""
    id: UUID
    user_id: UUID
    category_id: int
    created_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FavoriteWithCategory(BaseModel):
    """Respuesta con información de la categoría (opcional)"""
    id: UUID
    user_id: UUID
    category_id: int
    created_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FavoriteCategoryList(BaseModel):
    """Lista de IDs de categorías favoritas del usuario"""
    category_ids: List[int]