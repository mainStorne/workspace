import pytest
from httpx import ASGITransport, AsyncClient

from project.main import app

mark = pytest.mark.anyio


@pytest.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as cli:
        yield cli
