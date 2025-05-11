import asyncio
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from structlog import get_logger

from aibolit_app.api.middlewares.logging_middleware import LoggingMiddleware
from aibolit_app.api.transports.views.common.views import common_router
from aibolit_app.api.transports.views.schedules.views import schedules_router
from aibolit_app.grpc.main import make_grpc_server
from aibolit_app.logging import setup_logging
from aibolit_app.settings import get_app_settings, get_env_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_settings = get_app_settings()
    env_settings = get_env_settings()

    setup_logging(app_settings.app_environment)
    log = get_logger()
    await log.ainfo('API is starting')
    db_engine = create_async_engine(env_settings.database.sqlalchemy_url)
    db_sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    server = make_grpc_server(50051, db_sessionmaker, env_settings)
    await server.start()
    asyncio.create_task(server.wait_for_termination())  # noqa: RUF006
    yield {'db_engine': db_engine, 'db_sessionmaker': db_sessionmaker, 'settings': env_settings}
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

    app.include_router(schedules_router)
    app.include_router(common_router)

    return app
