# app/main.py
import uuid
import logging

import sentry_sdk
import structlog
from fastapi import FastAPI, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.routers import users, shops, orders, webhooks
# удалено: from loguru import logger
# удалено: from app.logger import logger
from app.logger import RequestIDMiddleware  # оставляем только саму мидлвару

# Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=settings.ENVIRONMENT,
    )

# structlog как единый логгер
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger("app")

# Импорт всех моделей (для create_all)
from app import models  # noqa

app = FastAPI(title="Coffee Aggregator API")

# Один middleware, который задаёт request_id
app.add_middleware(RequestIDMiddleware)

# Регистрация роутеров
app.include_router(webhooks.router)
app.include_router(users.router)
app.include_router(shops.router)
app.include_router(orders.router)

# Мидлвара для логирования (без повторной генерации request_id)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log.info("request_start", method=request.method, url=str(request.url), request_id=req_id)
    try:
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", req_id)
        log.info("request_complete", method=request.method, url=str(request.url), status=response.status_code, request_id=req_id)
        return response
    except Exception:
        log.exception("unhandled_exception", request_id=req_id)
        raise

@app.get("/health/db")
async def check_db_connection(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT now()"))
        time = result.scalar_one()
        return {"status": "ok", "time": str(time)}
    except Exception as e:
        return {"status": "error", "details": str(e)}

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("db_initialized")

@app.get("/error")
async def trigger_error():
    return 1 / 0

@app.get("/")
async def root():
    log.info("root_endpoint_called")
    return {"message": "Hello from FastAPI with Sentry + structlog!"}

if settings.SENTRY_DSN:
    app.add_middleware(SentryAsgiMiddleware)