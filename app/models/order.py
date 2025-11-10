import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Order(Base):
    __tablename__ = 'orders'


    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(UUID(as_uuid=True), ForeignKey("app_users.id", ondelete="CASCADE"))
    shop_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    time_slot_id = Column(UUID(as_uuid=True), ForeignKey("time_slots.id", ondelete="SET NULL"), nullable=True)
    slot_id = sa.Column(UUID(as_uuid=True), nullable=True)
    status = sa.Column(sa.String, nullable=False, default='new')
    preparation_due_at = sa.Column(sa.DateTime(timezone=True))
    currency = sa.Column(sa.String, nullable=True)
    subtotal = sa.Column(sa.Numeric)
    discount = sa.Column(sa.Numeric)
    total_amount = sa.Column(Integer, nullable=False, default=0)
    note_text = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime(timezone=True))
    paid_at = sa.Column(sa.DateTime(timezone=True))
    accepted_at = sa.Column(sa.DateTime(timezone=True))
    started_at = sa.Column(sa.DateTime(timezone=True))
    ready_at = sa.Column(sa.DateTime(timezone=True))
    completed_at = sa.Column(sa.DateTime(timezone=True))
    user = relationship("User", back_populates="orders")
    shop = relationship("Shop", back_populates="orders")
    slot = relationship("TimeSlot", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    slot_hold = relationship("SlotHold", back_populates="order", uselist=False)

