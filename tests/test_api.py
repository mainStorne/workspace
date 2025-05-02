from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends
from freezegun import freeze_time
from httpx import AsyncClient

from src import app
from src.api.deps.schedule_dependency import ScheduleRepository, get_schedule_repository, get_schedule_service
from src.api.schemas.schedule_schema import TakingsRead
from src.db import Schedule

from .utils import intake_start

pytestmark = pytest.mark.anyio


def assert_schedule(scheduled: datetime):
    assert 8 <= scheduled.hour <= 22
    if scheduled.hour == 22:
        assert scheduled.second == 0 and scheduled.minute == 0
    assert scheduled.minute % 15 == 0


# @freeze_time(intake_start)
# TODO: Can't monkeypatch datetime object because fastapi route saves usual type
@pytest.mark.skip
async def test_create_schedule(client: AsyncClient, session, monkeypatch):
    intake_finish = (intake_start + timedelta(days=3)).isoformat()
    with patch("src.api.schemas.schedule_schema.ScheduleCreate", MagicMock()):
        response = await client.post(
            "/schedule",
            json={
                "intake_period": "12",
                "medicine_name": "name",
                "user_id": 2,
                "intake_finish": intake_finish,
            },
        )
    assert response.status_code == 200
    schedule_id = response.json()["id"]
    schedule = await session.get(Schedule, schedule_id)
    assert schedule is not None


@freeze_time(intake_start)
@pytest.mark.parametrize(
    "schedule,schedules_count",
    [
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="15 20 * * *",
                intake_finish=None,
                intake_start=intake_start,
            ),
            1,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="*/5 21 * * *",
                intake_finish=None,
                intake_start=intake_start,
            ),
            4,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                intake_finish=None,
                intake_start=intake_start,
            ),
            14,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                intake_finish=intake_start + timedelta(hours=6),
                intake_start=intake_start,
            ),
            0,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                intake_finish=intake_start + timedelta(hours=22),
                intake_start=intake_start,
            ),
            14,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 9-15 * * *",
                intake_finish=intake_start + timedelta(hours=22),
                intake_start=intake_start,
            ),
            7,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                intake_finish=intake_start + timedelta(hours=10),
                intake_start=intake_start,
            ),
            2,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                intake_finish=intake_start + timedelta(hours=20),
                intake_start=intake_start,
            ),
            12,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period=f"0 * {(intake_start + timedelta(days=1)).day} * *",
                intake_finish=None,
                intake_start=intake_start,
            ),
            0,
        ),
    ],
)
async def test_schedule_period(schedule, client, session, schedules_count, monkeypatch):
    """
    Тестирование алгоритма выдачи приема таблеток с 8:00 - 22:00
    """  # noqa: RUF002

    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200
    assert len(response.json()) == schedules_count


@pytest.mark.parametrize("time_to_freeze", ["2025-03-14 00:00:00", "2025-03-15 12:00:00", "2026-03-15 12:00:00"])
async def test_expired_exception(schedule, client, time_to_freeze):
    """
    Тестирование ответа по запросу на истекшее расписание таблеток
    """
    with freeze_time(time_to_freeze):
        response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
        assert response.status_code == 400


async def test_intake_finish_none(schedule, client, session):
    schedule.intake_finish = None
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200


@freeze_time(intake_start)
@pytest.mark.parametrize(
    "schedule,schedules_count,days",
    [
        (
            Schedule(
                intake_period="10 */6 * * *",
                medicine_name="",
                intake_finish=None,
                user_id=1,
                intake_start=intake_start,
            ),
            16,
            8,
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_finish=None,
                user_id=1,
                intake_start=intake_start,
            ),
            12,
            6,
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_finish=intake_start + timedelta(days=3),
                user_id=1,
                intake_start=intake_start - timedelta(days=1),
            ),
            6,
            6,
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_start=intake_start,
                intake_finish=intake_start + timedelta(days=3, hours=22),
                user_id=1,
            ),
            8,
            6,
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_start=intake_start,
                intake_finish=intake_start + timedelta(days=3),
                user_id=1,
            ),
            6,
            6,
        ),
    ],
)
async def test_next_takings(schedule, client, session, schedules_count, days):
    async def mock_schedule_repository(schedule_service=Depends(get_schedule_service)):  # noqa: B008
        return ScheduleRepository(schedule_service, timedelta(days=days))

    app.dependency_overrides[get_schedule_repository] = mock_schedule_repository

    session.add(schedule)
    await session.commit()

    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    response_json = response.json()
    assert len(response_json) == schedules_count
    for raw in response_json:
        scheduled = TakingsRead.model_validate(raw)
        assert_schedule(scheduled.medicine_datetime)
