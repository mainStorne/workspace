from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from api.db import Schedule
from api.modules.schedule.schema import ScheduleCreate, TakingsRead

pytestmark = pytest.mark.anyio


now = datetime.now(tz=timezone.utc)


def assert_scheduled(scheduled: datetime):
    assert 8 <= scheduled.hour <= 22
    if scheduled.hour == 22:
        assert scheduled.second == 0 and scheduled.minute == 0
    assert scheduled.minute % 15 == 0


async def test_create_schedule(client, session):
    schedule = ScheduleCreate(
        medicine_name="name", intake_period="0 12 * * *", treatment_duration=timedelta(days=5), user_id=2
    )

    response = await client.post("/schedule", content=schedule.model_dump_json())
    assert response.status_code == 200
    schedule_id = response.json()["id"]
    schedule = await session.get(Schedule, schedule_id)
    assert schedule is not None


@pytest.mark.parametrize(
    "cron",
    [
        "* 12 * * *",  # intake period every minute in 12 hours every day
        "* * * * *",  # intake period every minute
        " * * * * * * * ",  # intake period every second with spaces
        "* * * * * * *",
        "* * * * * 2025",  # intake period every minute with spaces on specific year
        "15 * * * * 2025",  # intake period every 15 minute with spaces on specific year
        "15 8 * * *",  # intake period in 8 or 22 hours with not empty minutes
        "15 22 * * *",
    ],
)
async def test_wrong_schedules(client, cron):
    with pytest.raises(ValidationError):
        ScheduleCreate(medicine_name="name", intake_period=cron, treatment_duration=None, user_id=2)


@pytest.mark.parametrize(
    "cron,schedules_count",
    [("15 20 * * *", 1), ("*/5 21 * * *", 4), ("0 * * * *", 14), (f"0 * {(now + timedelta(days=1)).day} * *", 0)],
)
async def test_schedule_period(schedule, client, session, cron, schedules_count):
    """
    Пириод приема таблетков с 8:00 - 22:00
    #"""  # noqa: RUF002
    schedule.intake_period = cron
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200
    assert len(response.json()) == schedules_count


async def test_expired(schedule, client, monkeypatch):
    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return schedule.schedule_datetime + schedule.treatment_duration + timedelta(days=1)

    monkeypatch.setattr("api.modules.schedule.datetime", MockDateTime)
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 400


async def test_constantly(schedule, client, monkeypatch, session):
    schedule.treatment_duration = None
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "cron,schedules_count,days,now",
    [
        ("10 */6 * * *", 2, 8, datetime(year=now.year, month=now.month, day=now.day, hour=8)),
        ("0 */8 * * *", 2, 6, datetime(year=now.year, month=now.month, day=now.day, hour=7)),
    ],
)
async def test_next_takings(schedule, client, session, monkeypatch, cron, schedules_count, days, now):
    class MockSettings:
        NEXT_TAKINGS_PERIOD = timedelta(days=days)

    monkeypatch.setattr("api.modules.schedule.manager.settings", MockSettings)

    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr("api.modules.schedule.manager.datetime", MockDateTime)
    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == days
    for raw in response_json:
        scheduled = TakingsRead.model_validate(raw)
        assert_scheduled(scheduled.medicine_datetime)

    schedule_2 = Schedule(
        medicine_name="test2",
        intake_period=cron,  # 2 times per day + 1 time schedule first
        treatment_duration=None,
        user_id=schedule.user_id,
    )
    session.add(schedule_2)
    await session.commit()

    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    response_json = response.json()
    assert len(response_json) == days * (schedules_count + 1)  # one because the first schedule has one schedule per day
    for raw in response_json:
        scheduled = TakingsRead.model_validate(raw)
        assert_scheduled(scheduled.medicine_datetime)
