import sys
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger as log

# Чистим и настраиваем вывод
log.remove()
# JSON в stdout (удобно для docker/journalctl)
log.add(sys.stdout, level="INFO", serialize=True, enqueue=True)
# Логи в файл (если нужен отдельный файл)
log.add("webhook.log", level="INFO", rotation="10 MB", enqueue=True)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Берём X-Request-ID из заголовка, или генерим новый
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        req_log = log.bind(request_id=request_id)
        req_log.info("request_started", method=request.method, path=str(request.url.path))

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        req_log.info("request_finished", status=response.status_code)
        return response

logger = log