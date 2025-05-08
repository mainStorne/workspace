from datetime import timedelta

from fastapi import Depends
from freezegun import freeze_time
from httpx import AsyncClient
import pytest
from sqlmodel import select

from aibolit_app.api.depends import get_schedule_repo, get_schedule_service
from aibolit_app.api.schemas.schedules import ScheduleCard, TakingsRead
from aibolit_app.db import Schedule
from aibolit_app.services.schedules_service import ScheduleService
from tests.utils import zero_day_fixture

pytestmark = pytest.mark.anyio


@freeze_time(zero_day_fixture)
async def test_create_schedule(client: AsyncClient, session, monkeypatch):
    intake_finish = (zero_day_fixture + timedelta(days=3, hours=10)).isoformat()
    response = await client.post(
        '/schedule',
        json={
            'intake_period': '0 12 * * *',
            'medicine_name': 'name',
            'user_id': 2,
            'intake_start': (zero_day_fixture + timedelta(hours=8)).isoformat(),
            'intake_finish': intake_finish,
        },
    )
    assert response.status_code == 200
    schedule_id = response.json()['id']
    schedule = await session.get(Schedule, schedule_id)
    assert schedule is not None


@freeze_time(zero_day_fixture)
@pytest.mark.parametrize(
    'intake_start, intake_finish',
    [
        [zero_day_fixture, zero_day_fixture + timedelta(hours=10)],
        [
            zero_day_fixture + timedelta(hours=10),
            zero_day_fixture,
        ],
        [
            zero_day_fixture + timedelta(days=3, hours=10),
            zero_day_fixture + timedelta(hours=10),
        ],
        [
            zero_day_fixture - timedelta(days=3, hours=10),
            zero_day_fixture + timedelta(hours=10),
        ],
    ],
)
async def test_create_wrong_schedules(client, session, intake_start, intake_finish):
    response = await client.post(
        '/schedule',
        json={
            'intake_period': '0 12 * * *',
            'medicine_name': 'name',
            'user_id': 2,
            'intake_start': intake_start.isoformat(),
            'intake_finish': intake_finish.isoformat(),
        },
    )
    assert response.status_code == 422
    assert len((await session.exec(select(Schedule))).all()) == 0


@freeze_time(zero_day_fixture)
async def test_get_schedule(schedule_fixture, client, session):
    """
    Тестирование ответа по запросу на расписание приема таблеток
    """

    response = await client.get(
        '/schedule', params={'user_id': schedule_fixture.user_id, 'schedule_id': schedule_fixture.id}
    )
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    for raw in response_json:
        ScheduleCard.model_validate(raw)


async def test_schedule_on_doesnt_exist_schedule(client):
    response = await client.get('/schedule', params={'user_id': 0, 'schedule_id': 0})
    assert response.status_code == 404


@pytest.mark.parametrize('time_to_freeze', ['2025-03-14 00:00:00', '2025-03-15 12:00:00', '2026-03-15 12:00:00'])
async def test_schedule_expired(schedule_fixture, client, time_to_freeze):
    """
    Тестирование ответа по запросу на истекшее расписание таблеток
    """
    with freeze_time(time_to_freeze):
        response = await client.get(
            '/schedule', params={'user_id': schedule_fixture.user_id, 'schedule_id': schedule_fixture.id}
        )
        assert response.status_code == 400


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
async def test_next_takings(client, session, next_takings_period, expected, app_fixture):
    async def mock_schedule_service(schedule_repo=Depends(get_schedule_repo)):  # noqa: B008
        return ScheduleService(schedule_repo, next_takings_period)

    app_fixture.dependency_overrides[get_schedule_service] = mock_schedule_service

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

    response = await client.get('/next_takings', params={'user_id': 1})
    response_json = response.json()
    assert len(response_json) == len(expected)
    for raw, (schedule_idx, expected_datetime) in zip(response_json, expected):
        takings = TakingsRead.model_validate(raw)
        assert takings.id == schedule_fixture[schedule_idx].id
        assert takings.medicine_datetime == expected_datetime
