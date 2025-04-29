import asyncio
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from .filter_logging import filter_user_id_from_query_parameter
from .gRPC.server import Server
from .gRPC.servicers.schedule_servicer import ScheduleServiceServicer
from .middlewares.logging_middleware import LoggingMiddleware
from .modules import schedule

shared_processors = [
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    structlog.processors.TimeStamper(fmt=r"%Y-%m-%d %H:%M:%S", utc=True),
    structlog.processors.JSONRenderer(),
]


structlog.configure(
    processors=[structlog.contextvars.merge_contextvars, filter_user_id_from_query_parameter, *shared_processors],
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

formatter = structlog.stdlib.ProcessorFormatter(
    processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, *shared_processors],
)

handler = logging.StreamHandler()
# Use OUR `ProcessorFormatter` to format all `logging` entries.
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    server = Server(ScheduleServiceServicer(), 50051)
    await server.start()
    asyncio.create_task(server.wait_for_termination())  # noqa: RUF006
    yield
    await server.stop()


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)

app.include_router(schedule.r)
