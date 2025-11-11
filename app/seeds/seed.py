import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models import (
    Shop,
    MenuItem,
    ItemOptionGroup,
    ItemOption,
    TimeSlot
)

async def seed_data(db: AsyncSession):
    # === 1. Кофейни ===
    shops = [
        Shop(
            shop_name="Brew & Bean",
            address="ул. Арбат, 10",
            tz="Europe/Moscow",
            open_hours={"mon-fri": "08:00-20:00", "sat-sun": "09:00-18:00"},
            is_active=True
        ),
        Shop(
            shop_name="Daily Roast",
            address="ул. Тверская, 25",
            tz="Europe/Moscow",
            open_hours={"mon-fri": "07:30-21:00", "sat-sun": "09:00-19:00"},
            is_active=True
        ),
        Shop(
            shop_name="Coffee Republic",
            address="ул. Ленина, 5",
            tz="Europe/Moscow",
            open_hours={"mon-sun": "08:00-22:00"},
            is_active=True
        ),
        Shop(
            shop_name="Latte Lab",
            address="ул. Пушкина, 15",
            tz="Europe/Moscow",
            open_hours={"mon-fri": "08:00-19:00", "sat": "09:00-17:00"},
            is_active=True
        ),
        Shop(
            shop_name="Espresso Point",
            address="пр. Мира, 7",
            tz="Europe/Moscow",
            open_hours={"mon-sun": "08:30-21:00"},
            is_active=True
        ),
    ]
    db.add_all(shops)
    await db.commit()

    # === 2. Напитки ===
    drinks = [
        ("Американо", 150),
        ("Капучино", 200),
        ("Латте", 220),
        ("Флэт уайт", 230),
        ("Эспрессо", 120),
        ("Раф", 250),
        ("Мокко", 240),
        ("Матча латте", 260)
    ]

    menu_items = []
    for shop in shops:
        for name, price in drinks[:6]:  # 6 напитков в каждой кофейне
            item = MenuItem(
                shop_id=shop.id,
                item_name=name,
                base_price=price,
                is_active=True
            )
            db.add(item)
            await db.flush()  # получаем item.id до commit
            menu_items.append(item)

            # === 3. Опции ===
            size_group = ItemOptionGroup(
                menu_item_id=item.id,
                name="Размер",
                is_required=True
            )
            milk_group = ItemOptionGroup(
                menu_item_id=item.id,
                name="Молоко",
                is_required=False
            )
            db.add_all([size_group, milk_group])
            await db.flush()

            size_options = [
                ItemOption(group_id=size_group.id, name="Маленький", price_delta=0, is_available=True),
                ItemOption(group_id=size_group.id, name="Средний", price_delta=30, is_available=True),
                ItemOption(group_id=size_group.id, name="Большой", price_delta=50, is_available=True)
            ]
            milk_options = [
                ItemOption(group_id=milk_group.id, name="Обычное", price_delta=0, is_available=True),
                ItemOption(group_id=milk_group.id, name="Соевое", price_delta=40, is_available=True),
                ItemOption(group_id=milk_group.id, name="Безлактозное", price_delta=50, is_available=True)
            ]
            db.add_all(size_options + milk_options)
    await db.commit()

    # === 4. Тайм-слоты ===
    now = datetime.now()
    for shop in shops:
        slots = [
            TimeSlot(shop_id=shop.id, start=now.replace(hour=8, minute=0, second=0, microsecond=0), end=now.replace(hour=9, minute=0)),
            TimeSlot(shop_id=shop.id, start=now.replace(hour=9, minute=0, second=0, microsecond=0), end=now.replace(hour=10, minute=0)),
            TimeSlot(shop_id=shop.id, start=now.replace(hour=10, minute=0, second=0, microsecond=0), end=now.replace(hour=11, minute=0)),
        ]
        db.add_all(slots)
    await db.commit()

    print("✅ Seed data successfully inserted.")


async def main():
    async with AsyncSessionLocal() as db:
        await seed_data(db)

if __name__ == "__main__":
    asyncio.run(main())
