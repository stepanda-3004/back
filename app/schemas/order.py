# app/schemas/order.py
from pydantic import BaseModel, condecimal
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.schemas.order_item import OrderItemCreate, OrderItemRead
from app.schemas.payment import PaymentCreate, PaymentRead

class Order(BaseModel):
    user_id: Optional[UUID]
    shop_id: UUID
    slot_id: Optional[UUID]
    status: Optional[str] = "new"
    preparation_due_at: Optional[datetime] = None
    currency: Optional[str] = "RUB"
    subtotal: Optional[float] = 0.0
    discount: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    note: Optional[str] = None

class OrderCreate(Order):
    order_items: List[OrderItemCreate]
    payments: List[PaymentCreate]

class OrderUpdate(Order):
    pass

class OrderRead(Order):
    id: UUID
    created_at: datetime
    paid_at: Optional[datetime]
    accepted_at: Optional[datetime]
    started_at: Optional[datetime]
    ready_at: Optional[datetime]
    completed_at: Optional[datetime]

    order_items: Optional[List[OrderItemRead]] = []
    payments: Optional[List[PaymentRead]] = []

    class Config:
        orm_mode = True

class OrderSlotUpdate(BaseModel):
    slot_id: UUID

class AlternativeSlot(BaseModel):
    slot_id: UUID
    start: str  # ISO
    end: str
    remaining_capacity: Optional[int]  # None -> unlimited

class SlotFullError(BaseModel):
    error: str
    code: str
    alternatives: List[AlternativeSlot] = []