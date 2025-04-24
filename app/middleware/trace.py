# middleware.py
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from app.logger_context import trace_id_var


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = request.headers.get("X-Request-ID", str(uuid4()))
        trace_id_var.set(trace_id)  # 💡 Сохраняем в contextvar

        request.state.trace_id = trace_id

        from loguru import logger
        logger_ctx = logger.bind(trace_id=trace_id)
        request.state.logger = logger_ctx

        response = await call_next(request)
        response.headers["X-Request-ID"] = trace_id
        return response
