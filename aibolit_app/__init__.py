import asyncio
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from structlog import get_logger

from aibolit_app.api.middlewares.logging_middleware import LoggingMiddleware
from aibolit_app.api.transports.views.schedules import views
from aibolit_app.grpc.server import Server
from aibolit_app.grpc.servicers.schedule_servicer import ScheduleServiceServicer
from aibolit_app.logging import setup_logging
from aibolit_app.settings import get_env_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log = get_logger()
    await log.ainfo('API is starting')
    settings = get_env_settings()
    db_engine = create_async_engine(settings.database.sqlalchemy_url)
    db_sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    server = Server(ScheduleServiceServicer(), 50051)
    await server.start()
    asyncio.create_task(server.wait_for_termination())  # noqa: RUF006
    yield {'db_engine': db_engine, 'db_sessionmaker': db_sessionmaker}
    await db_engine.dispose()
    await server.stop()
    await log.ainfo('API is stopping')


def add_trace_documentation(
    trace_id: Annotated[UUID | None, Header(alias='X-Trace-Id')] = None,
    request_id: Annotated[UUID | None, Header(alias='X-Request-Id')] = None,
):
    return trace_id, request_id


def make_app():
    app = FastAPI(lifespan=lifespan, dependencies=[Depends(add_trace_documentation)])

    app.add_middleware(LoggingMiddleware)

    app.include_router(views.r)
    return app
