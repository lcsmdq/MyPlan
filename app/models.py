from datetime import datetime
import uuid
from sqlalchemy import UUID, Boolean, CheckConstraint, Column, ForeignKey, Integer, String, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from .database import Base
from enum import Enum

class Event(Base):
    __tablename__ = "events"
    created_by = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey("users.id"),  # <<<<<< ESTO DEBE SER 'users.id' (o el nombre real de tu tabla de usuarios)
        nullable=False,         
        index=True
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text)
    location_id = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    status = Column(Text, default='active')
    created_at = Column(DateTime)
    #category=Column(Integer)
    edited_at = Column(DateTime)

     

class EventWithLocationView(Base):
    __tablename__ = "events_with_location"
    __table_args__ = {'schema': 'public'}
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    location_id = Column(Integer)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
   #category = Column(Integer)
    location_name = Column(String)  # ✅ Campo extra de la vista
    created_by =  Column(UUID)
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<EventWithLocation(id={self.id}, location_id={self.location_id}, title={self.title})>"
    
'''
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
'''
class Assist(Base):
    __tablename__ = "assist"
    
    id = Column(UUID, primary_key=True,  default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('assist', 'like')", name='assist_status_check'),
        UniqueConstraint('user_id', 'event_id', 'status', name='unique_user_event_status'),
    )

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    
    # Información del usuario
    username = Column(String, unique=True, nullable=False)  # ✅ Con unique constraint
    email = Column(String, unique=True, nullable=False, index=True)  # ✅ Con unique constraint
    hashed_password = Column(String, nullable=False)
    
    # Roles y tipos
    role = Column(String, default='user', nullable=False)
    creator_type = Column(String, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.now, server_default=func.now(), nullable=False)
    
    # Extra info
    profile_picture = Column(String, nullable=True)
    bio = Column(String, nullable=True)

    # Constraints (ya están en la BD, pero los declaramos aquí también)
    __table_args__ = (
        CheckConstraint("role IN ('user', 'organizer', 'admin')", name='users_role_check'),
        CheckConstraint("creator_type IN ('comercio', 'planner', 'fundraiser') OR creator_type IS NULL", name='users_creator_type_check'),
    )
    
    # Relaciones
    # events = relationship("Event", back_populates="creator", cascade="all, delete-orphan")
    # assists = relationship("Assist", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
    
class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)  # ✅ Sin CASCADE
    category_id = Column(Integer,  nullable=False) # ForeignKey("categories.id"), Asumiendo que hay tabla categories
    created_at = Column(DateTime, default=datetime.now, server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # ✅ Soft delete para historial
    
    # Constraint para evitar duplicados activos (solo para favoritos no eliminados)
    __table_args__ = (
        UniqueConstraint('user_id', 'category_id', name='unique_user_category'),
    )
    
    def __repr__(self):
        return f"<Favorite user={self.user_id} category={self.category_id} deleted={self.deleted_at}>"