from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from pytest import fixture

import grpc
from src.db import Schedule
from src.grpc.generated.schedule_pb2 import (
    CreateScheduleRequest,
    GetNextTakingsRequest,
    GetScheduleIdsRequest,
    MakeScheduleRequest,
)
from src.grpc.generated.schedule_pb2_grpc import ScheduleServiceStub
from src.grpc.server import Server
from src.grpc.servicers.schedule_servicer import ScheduleServiceServicer
from tests.utils import zero_day_fixture

pytestmark = pytest.mark.anyio


@fixture(autouse=True, scope="session")
async def server():
    s = Server(port=50051, servicer=ScheduleServiceServicer())
    await s.start()
    yield
    await s.stop()


@fixture(autouse=True)
async def patch_session(session, monkeypatch):
    maker = MagicMock()
    maker.return_value.__aenter__.return_value = session
    monkeypatch.setattr("src.grpc.injections.schedule_inject.session_maker", maker)


@fixture()
async def stub():
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        yield ScheduleServiceStub(channel=channel)


async def test_create_schedule(stub, session):
    response = await stub.CreateSchedule(
        CreateScheduleRequest(user_id=1, medicine_name="test", intake_period="12", intake_finish=None)
    )

    assert response.id
    assert await session.get(Schedule, response.id) is not None


async def test_get_schedule_ids(stub, schedule_fixture, session):
    response = await stub.GetScheduleIds(GetScheduleIdsRequest(user_id=schedule_fixture.user_id))
    assert response.ids == [schedule_fixture.id]


@freeze_time(zero_day_fixture)
async def test_make_schedule(stub, schedule_fixture):
    response = await stub.MakeSchedule(
        MakeScheduleRequest(user_id=schedule_fixture.user_id, schedule_id=schedule_fixture.id)
    )
    assert len(response.items) == 1


@freeze_time(zero_day_fixture)
@pytest.mark.parametrize(
    "schedule_model,schedules_count,days",
    [
        (
            Schedule(
                intake_period="10 */6 * * *",
                medicine_name="",
                intake_finish=None,
                user_id=1,
                intake_start=zero_day_fixture,
            ),
            16,
            timedelta(8),
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_finish=None,
                user_id=1,
                intake_start=zero_day_fixture,
            ),
            12,
            timedelta(6),
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_finish=zero_day_fixture + timedelta(days=3),
                user_id=1,
                intake_start=zero_day_fixture - timedelta(days=1),
            ),
            6,
            timedelta(6),
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_start=zero_day_fixture,
                intake_finish=zero_day_fixture + timedelta(days=3, hours=22),
                user_id=1,
            ),
            8,
            timedelta(6),
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_start=zero_day_fixture,
                intake_finish=zero_day_fixture + timedelta(days=3),
                user_id=1,
            ),
            6,
            timedelta(6),
        ),
    ],
)
async def test_next_takings(stub, schedule_model, session, schedules_count, days, monkeypatch):
    settings_mock = MagicMock()
    settings_mock.NEXT_TAKINGS_PERIOD = days
    monkeypatch.setattr("src.grpc.injections.schedule_inject.settings", settings_mock)

    schedule = schedule_model
    session.add(schedule)
    await session.commit()
    response = await stub.GetNextTakings(GetNextTakingsRequest(user_id=schedule.user_id))
    assert len(response.items) == schedules_count
