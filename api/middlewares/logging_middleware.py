import time
from logging import DEBUG, INFO
from uuid import uuid4

import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger("name")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        structlog.contextvars.clear_contextvars()
        start_time = time.perf_counter_ns()
        trace_id = request.headers.get("X-TRACE-ID", str(uuid4()))
        span_id = str(uuid4())
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            span_id=span_id,
            method=request.method,
            path=request.url.path,
            query=request.url.query,
            request_id=request.headers.get("X-Request-Id", str(uuid4())),
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent"),
        )
        if log.is_enabled_for(DEBUG):
            await log.alog(DEBUG, "Request", headers=list(request.headers.items()))
        elif log.is_enabled_for(INFO):
            await log.alog(INFO, "Request")

        try:
            response = await call_next(request)

        except HTTPException as e:
            await log.ainfo(
                "Response",
                process_time=time.perf_counter_ns() - start_time,
                body_size=len(e.detail),
                status_code=e.status_code,
            )
            raise

        except Exception as e:
            await log.aexception(
                "Request failed",
                exc_info=e,
            )
            raise
        await log.ainfo(
            "Response",
            process_time=time.perf_counter_ns() - start_time,
            body_size=response.headers["content-length"],
            status_code=response.status_code,
        )
        return response
