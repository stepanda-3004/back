import sqlalchemy as sa
from sqlalchemy import Column,Text,Float, String, ForeignKey, Integer, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="SET NULL"))
    name_snapshot = Column(String, nullable=False)
    unit_price = Column(Float)
    qty = Column(Integer)
    line_total = Column(Float)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")
    options = relationship("OrderItemOption", back_populates="order_item", cascade="all, delete-orphan")
