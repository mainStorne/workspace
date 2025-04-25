from contextlib import asynccontextmanager

from fastapi import FastAPI

from .gRPC.server import Server
from .gRPC.servicers.schedule_server import ScheduleServiceServicer
from .modules import schedule


@asynccontextmanager
async def lifespan(app: FastAPI):
    server = Server(ScheduleServiceServicer(), 50051)
    await server.start()
    # asyncio.create_task(server.wait_for_termination())
    yield
    await server.stop()


app = FastAPI(lifespan=lifespan)

app.include_router(schedule.r)
