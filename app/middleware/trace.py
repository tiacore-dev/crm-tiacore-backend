from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.trace_id = trace_id

        # ⚠️ Важно: сохранить старый логгер и подменить loguru глобально
        from loguru import logger
        request.state._loguru_context = logger
        logger_ctx = logger.bind(trace_id=trace_id)
        request.state.logger = logger_ctx

        response = await call_next(request)
        response.headers["X-Request-ID"] = trace_id
        return response
