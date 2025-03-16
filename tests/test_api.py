from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from api.db import Schedule
from api.modules.schedule.schema import ScheduleCreate, TakingsRead

pytestmark = pytest.mark.anyio

now = datetime.now(tz=timezone.utc)
start_day = datetime(year=now.year, month=now.month, day=now.day, hour=0, tzinfo=timezone.utc)


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
async def test_wrong_schedules(cron):
    with pytest.raises(ValidationError):
        ScheduleCreate(medicine_name="name", intake_period=cron, treatment_duration=None, user_id=2)


async def test_negative_duration():
    with pytest.raises(ValidationError):
        ScheduleCreate(
            medicine_name="name",
            intake_period="0 * * * *",
            treatment_duration=timedelta(days=0, milliseconds=-1),
            user_id=2,
        )


@pytest.mark.parametrize(
    "schedule,schedules_count",
    [
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="15 20 * * *",
                treatment_duration=None,
                schedule_datetime=start_day,
            ),
            1,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="*/5 21 * * *",
                treatment_duration=None,
                schedule_datetime=start_day,
            ),
            4,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                treatment_duration=None,
                schedule_datetime=start_day,
            ),
            14,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                treatment_duration=timedelta(hours=6),
                schedule_datetime=start_day,
            ),
            0,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                treatment_duration=timedelta(hours=22),
                schedule_datetime=start_day,
            ),
            14,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 9-15 * * *",
                treatment_duration=timedelta(hours=22),
                schedule_datetime=start_day,
            ),
            7,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                treatment_duration=timedelta(hours=10),
                schedule_datetime=start_day,
            ),
            2,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period="0 * * * *",
                treatment_duration=timedelta(hours=20),
                schedule_datetime=start_day,
            ),
            12,
        ),
        (
            Schedule(
                medicine_name="",
                user_id=1,
                intake_period=f"0 * {(start_day + timedelta(days=1)).day} * *",
                treatment_duration=None,
                schedule_datetime=start_day,
            ),
            0,
        ),
    ],
)
async def test_schedule_period(schedule, client, session, schedules_count, monkeypatch):
    """
    Пириод приема таблетков с 8:00 - 22:00
    #"""  # noqa: RUF002

    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime(year=start_day.year, month=start_day.month, day=start_day.day, hour=0, tzinfo=timezone.utc)

    monkeypatch.setattr("api.modules.schedule.datetime", MockDateTime)
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200
    assert len(response.json()) == schedules_count


async def test_expired_exception(schedule, client, monkeypatch):
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
    "schedule,schedules_count,days",
    [
        (
            Schedule(intake_period="10 */6 * * *", medicine_name="", treatment_duration=None, user_id=1),
            16,
            8,
        ),
        (Schedule(intake_period="0 */8 * * *", medicine_name="", treatment_duration=None, user_id=1), 12, 6),
        (
            Schedule(
                intake_period="0 */8 * * *",
                medicine_name="",
                treatment_duration=timedelta(days=3),
                user_id=1,
                schedule_datetime=start_day - timedelta(days=1),
            ),
            4,
            6,
        ),
        (
            Schedule(intake_period="0 */8 * * *", medicine_name="", treatment_duration=timedelta(days=3), user_id=1),
            8,
            6,
        ),
    ],
)
async def test_next_takings(schedule, client, session, monkeypatch, schedules_count, days):
    class MockSettings:
        NEXT_TAKINGS_PERIOD = timedelta(days=days)

    monkeypatch.setattr("api.modules.schedule.manager.settings", MockSettings)

    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return start_day

    monkeypatch.setattr("api.modules.schedule.manager.datetime", MockDateTime)

    session.add(schedule)
    await session.commit()

    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    response_json = response.json()
    # one because the first schedule has one schedule per day
    assert len(response_json) == schedules_count
    for raw in response_json:
        scheduled = TakingsRead.model_validate(raw)
        assert_scheduled(scheduled.medicine_datetime)
