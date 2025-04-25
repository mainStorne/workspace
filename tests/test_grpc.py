from pytest import fixture


@fixture(autouse=True, scope="session")
async def server():
    pass


async def stub():
    pass


async def test_make_schedule():
    pass
