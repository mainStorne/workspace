from datetime import timedelta

from httpx import ASGITransport, AsyncClient
from pydantic._internal._generate_schema import GenerateSchema
from pydantic_core import core_schema
import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from aibolit_app.api.depends import get_db_depends
from aibolit_app.db import Schedule
from aibolit_app.main import make_app
from aibolit_app.settings import get_env_settings
from tests.utils import zero_day_fixture

pytestmark = pytest.mark.anyio


# fix pydantic patch error https://github.com/pydantic/pydantic/discussions/9343

initial_match_type = GenerateSchema.match_type


def match_type(self, obj):
    if getattr(obj, '__name__', None) == 'datetime':
        return core_schema.datetime_schema()
    return initial_match_type(self, obj)


GenerateSchema.match_type = match_type


@pytest.fixture(scope='session')
def settings():
    _settings = get_env_settings()
    _settings.database.db = 'test'
    return _settings


@pytest.fixture(scope='session')
def engine(settings):
    return create_async_engine(settings.database.sqlalchemy_url, plugins=['geoalchemy2'], poolclass=NullPool)


@pytest.fixture(scope='session')
def app_fixture():
    return make_app()


@pytest.fixture(scope='session')
async def client(app_fixture):
    async with AsyncClient(transport=ASGITransport(app_fixture), base_url='http://test') as cli:
        yield cli


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(autouse=True)
async def session(app_fixture, engine):
    async with engine.connect() as connection, connection.begin() as transaction:
        session = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode='create_savepoint')

        async def mock_get_session():
            async with session as s:
                yield s

        app_fixture.dependency_overrides[get_db_depends] = mock_get_session
        async with session as s:
            yield s
        await transaction.rollback()


@pytest.fixture()
async def schedule_fixture(session):
    _schedule = Schedule(
        medicine_name='test',
        intake_period='8 12 * * *',
        user_id=1,
        intake_finish=zero_day_fixture + timedelta(days=1),
        intake_start=zero_day_fixture,
    )
    session.add(_schedule)
    await session.commit()
    return _schedule
