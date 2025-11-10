# app/routers/order.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from uuid import UUID
from typing import List
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate
from app.crud.order import list_orders, get_order, create_order, update_order, delete_order
from app.core.database import get_db
from app import crud, schemas
from app.models.order import Order
from app.models.time_slot import TimeSlot
from app.models.slot_hold import SlotHold
from typing import List
from app.schemas.menu_item import MenuItemBase, MenuItemRead
from app.schemas.order import (
    OrderCreate,
    OrderRead,
    OrderUpdate,
    OrderSlotUpdate,
    AlternativeSlot
)

from app.crud.slot import (
    get_slot,
    remaining_capacity,
    create_hold,
    find_alternative_slots,
    cleanup_expired_holds
)

logger = logging.getLogger("routers.order")
router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/", response_model=List[OrderRead])
async def route_list_orders(shop_id: UUID = None, db: AsyncSession = Depends(get_db)):
    orders = await list_orders(db, shop_id=shop_id)
    return orders

@router.get("/{order_id}", response_model=OrderRead)
async def route_get_order(order_id: UUID, db: AsyncSession = Depends(get_db)):
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order

@router.post("/", response_model=OrderRead, status_code=201)
async def route_create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    new_order = await create_order(db, payload)
    return new_order

@router.put("/{order_id}", response_model=OrderRead)
async def route_update_order(order_id: UUID, payload: OrderUpdate, db: AsyncSession = Depends(get_db)):
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    updated = await update_order(db, order, payload)
    return updated

@router.delete("/{order_id}", response_model=OrderRead)
async def route_delete_order(order_id: UUID, db: AsyncSession = Depends(get_db)):
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    deleted = await delete_order(db, order)
    return deleted

# === MENU ITEMS ===
@router.post("/menu", response_model=schemas.MenuItemBase)
async def create_menu_item(item_in: schemas.MenuItemCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Creating menu item {item_in.name} for shop={item_in.shop_id}")
    return await crud.menu_item.create(db, item_in)


@router.get("/menu", response_model=List[schemas.MenuItemBase])
async def list_menu_items(db: AsyncSession = Depends(get_db)):
    logger.info("Listing menu items")
    return await crud.menu_item.get_multi(db)


# === TIME SLOTS ===
@router.post("/slots", response_model=schemas.TimeSlot)
async def create_time_slot(slot_in: schemas.TimeSlotCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Creating timeslot for shop={slot_in.shop_id}")
    return await crud.time_slot.create(db, slot_in)

@router.get("/slots", response_model=List[schemas.TimeSlot])
async def list_time_slots(db: AsyncSession = Depends(get_db)):
    logger.info("Listing time slots")
    return await crud.time_slot.get_multi(db)

@router.patch("/{order_id}/slot", response_model=dict)
async def patch_order_slot(order_id: str, payload: OrderSlotUpdate, db: AsyncSession = Depends(get_db)):
    """
    Установить слот для заказа (создаёт hold на 120s). 
    Если слот переполнен — вернёт 409 и 3 ближайших альтернативных слота.
    """
    start_t = datetime.utcnow()
    # 1. Проверим заказ
    q = await db.execute(select(Order).where(Order.id == order_id))
    order = q.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2. Получим слот
    slot = await get_slot(db, payload.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    # 3. Lazy cleanup expired holds
    await cleanup_expired_holds(db)

    # 4. Проверим capacity
    rem = await remaining_capacity(db, slot)
    if rem is not None and rem <= 0:
        # слот переполнен — найдём альтернативы
        now = datetime.utcnow()
        candidates = await find_alternative_slots(db, slot.shop_id, now, limit=10)
        alts = []
        for c in candidates:
            c_rem = await remaining_capacity(db, c)
            if c_rem is None or c_rem > 0:
                alts.append(AlternativeSlot(
                    slot_id=c.id,
                    start=c.start.isoformat() if c.start else None,
                    end=c.end.isoformat() if c.end else None,
                    remaining_capacity=c_rem
                ))
            if len(alts) >= 3:
                break
        raise HTTPException(
            status_code=409,
            detail={"error": "slot_full", "code": "slot_full", "alternatives": [a.dict() for a in alts]}
        )

    # 5. Есть место — создаём hold + записываем в order
    hold = await create_hold(db, slot.id, order.id)
    # set order.slot_id and preparation_due_at
    # подготовка: можем выставить preparation_due_at как min(slot.start, now + 10min) или slot.start - lead_time
    now = datetime.utcnow()
    lead = timedelta(minutes=10)
    prep_due = slot.start if slot.start and slot.start > (now + lead) else (now + lead)
    order.slot_id = slot.id
    order.preparation_due_at = prep_due

    db.add(order)
    db.add(hold)
    await db.commit()

    duration_ms = (datetime.utcnow() - start_t).total_seconds() * 1000
    logger.info(f"order {order_id}: slot assigned {slot.id} (hold id={hold.id}) in {duration_ms:.2f}ms")
    return {"status": "ok", "order_id": str(order.id), "slot_id": str(slot.id), "hold_expires_at": hold.expires_at.isoformat()}