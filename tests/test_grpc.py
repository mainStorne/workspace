from contextlib import asynccontextmanager
from datetime import timedelta, timezone

from freezegun import freeze_time
from google.protobuf.timestamp import Timestamp
import grpc
import pytest
from pytest import fixture

from aibolit_app.db import Schedule
from aibolit_app.grpc.generated.schedule_pb2 import (
    CreateScheduleRequest,
    GetNextTakingsRequest,
    GetScheduleIdsRequest,
    MakeScheduleRequest,
)
from aibolit_app.grpc.generated.schedule_pb2_grpc import ScheduleServiceStub
from aibolit_app.grpc.main import make_grpc_server
from aibolit_app.integrations.schedules_repo import ScheduleRepo
from aibolit_app.services.schedules_service import ScheduleService
from tests.utils import zero_day_fixture

pytestmark = pytest.mark.anyio


@fixture(autouse=True)
async def server(engine, settings, session):
    @asynccontextmanager
    async def mock_session_maker(*args, **kwargs):
        yield session

    s = make_grpc_server(50051, settings=settings, db_session_maker=mock_session_maker)
    await s.start()
    yield
    await s.stop()


@fixture()
async def stub():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        yield ScheduleServiceStub(channel=channel)


@freeze_time(zero_day_fixture)
async def test_create_schedule(stub, session):
    intake_start = Timestamp()
    intake_start.FromDatetime(zero_day_fixture + timedelta(hours=8))
    intake_finish = Timestamp()
    intake_finish.FromDatetime(zero_day_fixture + timedelta(days=2, hours=10))
    response = await stub.CreateSchedule(
        CreateScheduleRequest(
            user_id=1,
            medicine_name='test',
            intake_period='0 12 * * *',
            intake_finish=intake_finish,
            intake_start=intake_start,
        )
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
    'next_takings_period, expected',
    [
        [
            timedelta(days=1),
            [
                (0, zero_day_fixture + timedelta(hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(hours=18, minutes=15)),
                (1, zero_day_fixture + timedelta(hours=8)),
                (1, zero_day_fixture + timedelta(hours=16)),
            ],
        ],
        [
            timedelta(days=2),
            [
                (0, zero_day_fixture + timedelta(hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(hours=18, minutes=15)),
                (0, zero_day_fixture + timedelta(days=1, hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(days=1, hours=18, minutes=15)),
                (1, zero_day_fixture + timedelta(hours=8)),
                (1, zero_day_fixture + timedelta(hours=16)),
                (1, zero_day_fixture + timedelta(days=1, hours=8)),
                (1, zero_day_fixture + timedelta(days=1, hours=16)),
            ],
        ],
        [
            timedelta(days=3),
            [
                (0, zero_day_fixture + timedelta(hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(hours=18, minutes=15)),
                (0, zero_day_fixture + timedelta(days=1, hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(days=1, hours=18, minutes=15)),
                (0, zero_day_fixture + timedelta(days=2, hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(days=2, hours=18, minutes=15)),
                (1, zero_day_fixture + timedelta(hours=8)),
                (1, zero_day_fixture + timedelta(hours=16)),
                (1, zero_day_fixture + timedelta(days=1, hours=8)),
                (1, zero_day_fixture + timedelta(days=1, hours=16)),
                (1, zero_day_fixture + timedelta(days=2, hours=8)),
                (1, zero_day_fixture + timedelta(days=2, hours=16)),
            ],
        ],
        [
            timedelta(days=4),
            [
                (0, zero_day_fixture + timedelta(hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(hours=18, minutes=15)),
                (0, zero_day_fixture + timedelta(days=1, hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(days=1, hours=18, minutes=15)),
                (0, zero_day_fixture + timedelta(days=2, hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(days=2, hours=18, minutes=15)),
                (0, zero_day_fixture + timedelta(days=3, hours=12, minutes=15)),
                (0, zero_day_fixture + timedelta(days=3, hours=18, minutes=15)),
                (1, zero_day_fixture + timedelta(hours=8)),
                (1, zero_day_fixture + timedelta(hours=16)),
                (1, zero_day_fixture + timedelta(days=1, hours=8)),
                (1, zero_day_fixture + timedelta(days=1, hours=16)),
                (1, zero_day_fixture + timedelta(days=2, hours=8)),
                (1, zero_day_fixture + timedelta(days=2, hours=16)),
            ],
        ],
    ],
)
async def test_next_takings(stub, session, next_takings_period, expected, settings, monkeypatch):
    settings.next_takings_period = next_takings_period

    @asynccontextmanager
    async def mock_schedule_service_dependency(self):
        yield ScheduleService(
            ScheduleRepo(session, self._settings.schedule_lowest_bound, self._settings.schedule_highest_bound),
            self._settings.next_takings_period,
        )

    monkeypatch.setattr(
        'aibolit_app.grpc.servicers.schedule_servicer.ScheduleServiceServicer.schedule_service_dependency',
        mock_schedule_service_dependency,
    )

    schedule_fixture = [
        Schedule(
            intake_period='10 */6 * * *',
            medicine_name='0',
            intake_finish=None,
            user_id=1,
            intake_start=zero_day_fixture,
        ),
        Schedule(
            intake_period='0 */8 * * *',
            medicine_name='1',
            intake_start=zero_day_fixture - timedelta(days=1),
            intake_finish=zero_day_fixture + timedelta(days=3),
            user_id=1,
        ),
    ]
    for schedule in schedule_fixture:
        session.add(schedule)
    await session.commit()

    response = await stub.GetNextTakings(GetNextTakingsRequest(user_id=1))
    assert len(response.items) == len(expected)
    for takings, (schedule_idx, expected_datetime) in zip(response.items, expected):
        assert takings.id == schedule_fixture[schedule_idx].id
        assert takings.medicine_datetime.ToDatetime(timezone.utc) == expected_datetime
