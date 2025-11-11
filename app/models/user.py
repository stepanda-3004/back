import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = 'app_users'


    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = sa.Column(sa.String, nullable=True)
    email = sa.Column(sa.String, nullable=True)
    display_name = sa.Column(sa.String, nullable=True)
    city = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True))
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
