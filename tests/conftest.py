from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src import app
from src.api.deps.session_dependency import get_session
from src.conf import settings
from src.db import Schedule

pytestmark = pytest.mark.anyio
engine = create_async_engine(settings.database.sqlalchemy_url, plugins=["geoalchemy2"], poolclass=NullPool)
session_maker = async_sessionmaker(
    bind=engine, expire_on_commit=False, join_transaction_mode="create_savepoint", class_=AsyncSession
)


@pytest.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as cli:
        yield cli


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def session():
    async with engine.connect() as connection, connection.begin() as transaction:
        session = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")

        async def mock_get_session():
            async with session as s:
                yield s

        app.dependency_overrides[get_session] = mock_get_session
        async with session as s:
            yield s
        await transaction.rollback()


@pytest.fixture()
async def schedule(session):
    intake_start = datetime(year=2025, month=3, day=13, hour=0, tzinfo=timezone.utc)
    _schedule = Schedule(
        medicine_name="test",
        intake_period="8 12 * * *",
        user_id=1,
        intake_finish=intake_start + timedelta(days=1),
        intake_start=intake_start,
    )
    session.add(_schedule)
    await session.commit()
    return _schedule
