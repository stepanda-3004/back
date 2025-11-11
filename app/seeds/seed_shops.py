import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.shop import Shop  # убедись, что путь верный
from app.core.database import Base

# ✅ Используем синхронный URL, который уже есть в config
engine = create_engine(settings.DATABASE_URL_SYNC)

SessionLocal = sessionmaker(bind=engine)

def seed_shops():
    session = SessionLocal()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE_DIR, "shops.json"), "r", encoding="utf-8") as f:
        shops = json.load(f)

    for shop in shops:
        shop_obj = Shop(
            id=shop["id"],
            shop_name=shop["shop_name"],
            address=shop["address"],
            lat=float(shop["lat"]) if shop["lat"] else None,
            lng=float(shop["lng"]) if shop["lng"] else None,
            tz=shop["tz"],
            open_hours=shop["open_hours"],  # JSON в колонку JSON
            is_active=shop["is_active"],
            created_at=shop.get("created_at"),
        )

        session.merge(shop_obj)  # UPSERT (insert or update)

    session.commit()
    session.close()
    print("✅ Shops inserted successfully!")


if __name__ == "__main__":
    seed_shops()
