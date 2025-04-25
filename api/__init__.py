import asyncio
from contextlib import asynccontextmanager
from logging import INFO, basicConfig

from fastapi import FastAPI

from .gRPC.server import Server
from .gRPC.servicers.schedule_server import ScheduleServiceServicer
from .middlewares.logging_middleware import LoggingMiddleware
from .modules import schedule

basicConfig(level=INFO)


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
