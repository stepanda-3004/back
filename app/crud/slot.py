# app/crud/slot.py
from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.time_slot import TimeSlot
from app.models.slot_hold import SlotHold
from app.models.order import Order
from app.logger import logger
from uuid import UUID

HOLD_TTL_SECONDS = 120

async def cleanup_expired_holds(db: AsyncSession):
    now = datetime.utcnow()
    q = delete(SlotHold).where(SlotHold.expires_at <= now)
    res = await db.execute(q)
    await db.commit()
    logger.debug("slot: cleaned expired holds")

async def count_active_holds(db: AsyncSession, slot_id: UUID) -> int:
    now = datetime.utcnow()
    q = select(func.count()).select_from(SlotHold).where(
        and_(SlotHold.slot_id == slot_id, SlotHold.expires_at > now)
    )
    result = await db.execute(q)
    return int(result.scalar() or 0)

async def count_confirmed_orders(db: AsyncSession, slot_id: UUID) -> int:
    # считать за «занятые» все заказы, у которых slot_id совпадает и статус != cancelled
    q = select(func.count()).select_from(Order).where(
        and_(Order.slot_id == slot_id, Order.status != "cancelled")
    )
    result = await db.execute(q)
    return int(result.scalar() or 0)

async def get_slot(db: AsyncSession, slot_id: UUID) -> TimeSlot | None:
    q = select(TimeSlot).where(TimeSlot.id == slot_id)
    result = await db.execute(q)
    return result.scalar_one_or_none()

async def create_hold(db: AsyncSession, slot_id: UUID, order_id: UUID) -> SlotHold:
    now = datetime.utcnow()
    hold = SlotHold(slot_id=slot_id, order_id=order_id, expires_at=now + timedelta(seconds=HOLD_TTL_SECONDS))
    db.add(hold)
    await db.flush()
    # do not commit here necessarily (caller may commit); but we will commit in endpoint
    return hold

async def remaining_capacity(db: AsyncSession, slot: TimeSlot) -> int | None:
    # returns None for unlimited
    if slot.capacity is None:
        return None
    await cleanup_expired_holds(db)
    holds = await count_active_holds(db, slot.id)
    orders = await count_confirmed_orders(db, slot.id)
    used = holds + orders
    rem = slot.capacity - used
    return rem

async def find_alternative_slots(db: AsyncSession, shop_id, now_dt: datetime, limit: int = 10) -> List[TimeSlot]:
    # ближайшие слоты в будущем по shop_id
    q = select(TimeSlot).where(
        and_(TimeSlot.shop_id == shop_id, TimeSlot.start >= now_dt)
    ).order_by(TimeSlot.start.asc()).limit(limit)
    res = await db.execute(q)
    return res.scalars().all()
