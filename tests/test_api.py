from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends
from freezegun import freeze_time
from httpx import AsyncClient

from src import app
from src.api.depends import get_schedule_repo, get_schedule_service
from src.api.schemas.schedules import ScheduleCard, TakingsRead
from src.db import Schedule
from src.services.schedules_service import ScheduleService
from tests.utils import day_with_zero_hour

pytestmark = pytest.mark.anyio


# @freeze_time(intake_start)
# TODO: Can't monkeypatch datetime object because fastapi route saves usual type
@pytest.mark.skip
async def test_create_schedule(client: AsyncClient, session, monkeypatch):
    intake_finish = (day_with_zero_hour + timedelta(days=3)).isoformat()
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


@freeze_time(day_with_zero_hour)
async def test_schedule_period(schedule, client, session):
    """
    Тестирование ответа по запросу на расписание приема таблеток
    """

    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    for raw in response_json:
        ScheduleCard.model_validate(raw)


async def test_not_exists_schedule(client):
    response = await client.get("/schedule", params={"user_id": 0, "schedule_id": 0})
    assert response.status_code == 404


@pytest.mark.parametrize("time_to_freeze", ["2025-03-14 00:00:00", "2025-03-15 12:00:00", "2026-03-15 12:00:00"])
async def test_expired_exception(schedule, client, time_to_freeze):
    """
    Тестирование ответа по запросу на истекшее расписание таблеток
    """
    with freeze_time(time_to_freeze):
        response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
        assert response.status_code == 400


@freeze_time(day_with_zero_hour)
@pytest.mark.parametrize(
    "schedule,schedules_count,days",
    [
        (
            Schedule(
                intake_period="10 */6 * * *",
                medicine_name="",
                intake_finish=None,
                user_id=1,
                intake_start=day_with_zero_hour,
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
                intake_start=day_with_zero_hour,
            ),
            12,
            6,
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_finish=day_with_zero_hour + timedelta(days=3),
                user_id=1,
                intake_start=day_with_zero_hour - timedelta(days=1),
            ),
            6,
            6,
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_start=day_with_zero_hour,
                intake_finish=day_with_zero_hour + timedelta(days=3, hours=22),
                user_id=1,
            ),
            8,
            6,
        ),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                intake_start=day_with_zero_hour,
                intake_finish=day_with_zero_hour + timedelta(days=3),
                user_id=1,
            ),
            6,
            6,
        ),
    ],
)
async def test_next_takings(schedule, client, session, schedules_count, days):
    async def mock_schedule_service(schedule_repo=Depends(get_schedule_repo)):  # noqa: B008
        return ScheduleService(schedule_repo, timedelta(days=days))

    app.dependency_overrides[get_schedule_service] = mock_schedule_service

    session.add(schedule)
    await session.commit()

    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    response_json = response.json()
    assert len(response_json) == schedules_count
    for raw in response_json:
        TakingsRead.model_validate(raw)
