from contextvars import ContextVar
from logging import getLogger
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

log = getLogger("uvicorn")
log.propagate = False
span_id_var = ContextVar("span_id")
trace_id_var = ContextVar("trace_id")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id", str(uuid4()))
        trace_id_var.set(trace_id)
        span_id = str(uuid4())
        span_id_var.set(span_id)
        log.info(
            "Request trace_id: %s, span_id: %s, method: %s, url: %s", trace_id, span_id, request.method, request.url
        )
        try:
            response = await call_next(request)
        except Exception as e:
            log.exception(
                exc_info=e,
                message="trace_id: %s, span_id: %s, method: %s, url: %s"  # noqa: UP031
                % (
                    trace_id,
                    span_id,
                    request.method,
                    request.url,
                ),
            )
            raise

        log.info(
            "Response trace_id: %s, span_id: %s, method: %s, url: %s", trace_id, span_id, request.method, request.url
        )
        return response
