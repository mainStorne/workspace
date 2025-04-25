from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware

request_id = ContextVar("request_id")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id.set("123")
        response = await call_next(request)
        return response
