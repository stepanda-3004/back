# app/crud/order.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.item_option import ItemOption
from app.schemas.order import OrderCreate, OrderUpdate
from app.schemas.order_item import OrderItemCreate
from app.schemas.payment import PaymentCreate
from app.crud.base import get_all, get_by_id, create_instance, update_instance, delete_instance
from app.models import (
    Order, OrderItem, OrderItemOption,
    Payment, TimeSlot, MenuItem, ItemOptionGroup, ItemOption
)
from app.schemas import (
    OrderCreate, OrderItemCreate, OrderItemOptionCreate,
    PaymentCreate, TimeSlotCreate, MenuItemCreate,
    ItemOptionGroupCreate, ItemOptionCreate
)
from app.crud.base import CRUDBase


logger = logging.getLogger("crud.order")

async def list_orders(db: AsyncSession, shop_id=None):
    if shop_id:
        q = await db.execute(select(Order).where(Order.shop_id == shop_id))
        return q.scalars().all()
    return await get_all(db, Order)

async def get_order(db: AsyncSession, order_id):
    # load order and relationships if needed (refresh)
    return await get_by_id(db, Order, order_id)

async def create_order(db: AsyncSession, order_in: OrderCreate):

    try:
        # create main order
        order_data = order_in.model_dump(exclude={"order_items", "payments"})
        order = Order(**order_data)
        db.add(order)
        await db.flush()  # assign PK to order

        # create items
        for item in order_in.order_items:
            # create main OrderItem
            item_data = item.model_dump()
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_data["menu_item_id"],
                name_snapshot=item_data["name_snapshot"],
                unit_price=item_data["unit_price"],
                qty=item_data["qty"],
                line_total=item_data["line_total"],
            )
            db.add(order_item)
            await db.flush()
            # handle passed option ids: create order_item_options rows
            option_ids = item_data.get("options") or []
            # If your model OrderItemOption exists and named OrderItemOption, import and create similarly
            if option_ids:
                from app.models.order_item_option import OrderItemOption
                for opt_id in option_ids:
                    oio = OrderItemOption(
                        order_item_id=order_item.id,
                        option_id=opt_id,
                        name_snapshot=None,
                        price_delta=None,
                    )
                    db.add(oio)

        # create payments
        for p in order_in.payments:
            pdata = p.model_dump()
            pay = Payment(
                order_id=order.id,
                method=pdata["method"],
                status=pdata.get("status"),
                amount=pdata["amount"],
                provider_id=pdata.get("provider_id"),
                extra=pdata.get("extra"),
            )
            db.add(pay)

        await db.commit()
        await db.refresh(order)
        return order
    except Exception:
        logger.exception("create_order failed")
        await db.rollback()
        raise

async def update_order(db: AsyncSession, order_obj, order_in: OrderUpdate):
    try:
        return await update_instance(db, order_obj, order_in.model_dump(exclude_none=True))
    except Exception:
        logger.exception("update_order failed")
        raise

async def delete_order(db: AsyncSession, order_obj):
    try:
        return await delete_instance(db, order_obj)
    except Exception:
        logger.exception("delete_order failed")
        raise

class CRUDMenuItem(CRUDBase[MenuItem, MenuItemCreate, MenuItemCreate]):
    async def create(self, db: AsyncSession, obj_in: MenuItemCreate) -> MenuItem:
        db_item = MenuItem(
            shop_id=obj_in.shop_id,
            name=obj_in.name,
            description=obj_in.description,
            image_url=obj_in.image_url,
            base_price=obj_in.base_price,
            is_active=obj_in.is_active,
            sort_order=obj_in.sort_order,
        )
        db.add(db_item)
        await db.flush()

        # Каскад: option groups → options
        for group_in in obj_in.option_groups or []:
            db_group = ItemOptionGroup(
                menu_item_id=db_item.id,
                name=group_in.name,
                min_select=group_in.min_select,
                max_select=group_in.max_select,
                is_required=group_in.is_required,
                sort_order=group_in.sort_order,
            )
            db.add(db_group)
            await db.flush()

            for opt_in in group_in.options or []:
                db_opt = ItemOption(
                    group_id=db_group.id,
                    name=opt_in.name,
                    price_delta=opt_in.price_delta,
                    is_default=opt_in.is_default,
                    sort_order=opt_in.sort_order,
                    is_available=opt_in.is_available,
                )
                db.add(db_opt)

        await db.flush()
        return db_item


class CRUDTimeSlot(CRUDBase[TimeSlot, TimeSlotCreate, TimeSlotCreate]):
    pass

menu_item = CRUDMenuItem(MenuItem)
time_slot = CRUDTimeSlot(TimeSlot)