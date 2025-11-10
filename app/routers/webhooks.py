from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import get_settings, Settings
from app.models.webhook_event import WebhookEvent
from app.logger import logger
from datetime import datetime
import os
import hmac
import hashlib

# 🔐 Секрет, который будет использоваться для проверки подписи
# (Ты можешь взять его из .env)
SECRET_TOKEN = os.getenv("WEBHOOK_SECRET")


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

router = APIRouter(prefix="/webhook", tags=["Webhook"])

@router.post("/order-status")
async def receive_order_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        start = datetime.utcnow()

        # ✅ Проверяем подпись
        signature = request.headers.get("X-Signature")
        if signature != SECRET_TOKEN:
            logger.warning(f"[WEBHOOK] Invalid signature: {signature}")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # ✅ Читаем тело запроса
        payload = await request.json()
        event_type = payload.get("event") or "unknown"

        logger.info(f"[WEBHOOK] Received: {event_type}, payload={payload}")

        # ✅ Сохраняем в базу данных
        webhook_event = WebhookEvent(event_type=event_type, payload=payload)
        db.add(webhook_event)
        await db.commit()

        duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        logger.info(f"[WEBHOOK] saved to DB in {duration_ms:.2f} ms")

        return {"status": "ok"}  # MUST reply <1 sec

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WEBHOOK] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.get("/events")
async def list_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WebhookEvent).order_by(WebhookEvent.received_at.desc()))
    return result.scalars().all()

@router.post("/payments", status_code=200)
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    body = await request.body()
    signature = request.headers.get("X-Signature")

    if not verify_signature(body, signature, settings.PAYMENT_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    # обработка логики success/failed
    payment_id = payload.get("payment_id")
    status = payload.get("status")

    if status == "paid":
        await mark_order_paid(db, payment_id)
    elif status == "failed":
        await mark_order_failed(db, payment_id)

    return {"status": "OK"}
