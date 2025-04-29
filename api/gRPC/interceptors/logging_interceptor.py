import time
from uuid import uuid4

import grpc
import structlog
from grpc_interceptor import AsyncServerInterceptor
from structlog import get_logger
from structlog.stdlib import BoundLogger

log: BoundLogger = get_logger()


class LoggingInterceptor(AsyncServerInterceptor):
    async def intercept(self, method, request_or_iterator, context: grpc.aio.ServicerContext, method_name):
        start_time = time.perf_counter_ns()
        structlog.contextvars.clear_contextvars()
        metadata = context.invocation_metadata()

        metadata = dict(metadata) if metadata else {}
        trace_id = metadata.get("X-TRACE-ID", str(uuid4()))
        request_id = metadata.get("X-Request-Id", str(uuid4()))
        span_id = str(uuid4())
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            span_id=span_id,
            request_id=request_id,
            ip_address=context.peer().split(":")[1],
            user_agent=metadata.get("user-agent"),
        )

        await log.ainfo("Request")

        try:
            response = await method(request_or_iterator, context)

        except grpc.aio.BaseError as e:
            await log.aexception("Non-OK Status in controller", exc_info=e)
            raise
        except Exception as e:
            await log.aerror("Exception in request handler", exc_info=e)
            await context.abort(grpc.StatusCode.UNKNOWN, "Unknown exception")
            return

        await log.ainfo(
            "Response",
            process_time=time.perf_counter_ns() - start_time,
            body_size=response.ByteSize(),
        )
        context.set_trailing_metadata((
            ("x-trace-id", trace_id),
            ("x-request-id", request_id),
        ))
        return response
