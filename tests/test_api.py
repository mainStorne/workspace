from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from api.db import Schedule
from api.modules.schedule.schema import ScheduleCreate, TakingsRead

pytestmark = pytest.mark.anyio

now = datetime.now(tz=timezone.utc)
intake_start = datetime(year=now.year, month=now.month, day=now.day, hour=0, tzinfo=timezone.utc)


def assert_scheduled(scheduled: datetime):
    assert 8 <= scheduled.hour <= 22
    if scheduled.hour == 22:
        assert scheduled.second == 0 and scheduled.minute == 0
    assert scheduled.minute % 15 == 0


async def test_create_schedule(client, session):
    schedule = ScheduleCreate(
        medicine_name="name",
        intake_period="12",
        intake_finish=intake_start + timedelta(days=5),
        user_id=2,
        intake_start=intake_start,
    )
    # create json so because schedule schema created intake_period in full form of cron syntax during initialization
    response = await client.post(
        "/schedule",
        json={
            "intake_period": "12",
            "medicine_name": "name",
            "user_id": 2,
            "intake_start": intake_start.isoformat(),
            "intake_finish": (intake_start + timedelta(days=3)).isoformat(),
        },
    )
    assert response.status_code == 200
    schedule_id = response.json()["id"]
    schedule = await session.get(Schedule, schedule_id)
    assert schedule is not None


@pytest.mark.parametrize(
    "cron",
    [
        "23",  # intake period in 8 or 22 hours
    ],
)
async def test_wrong_schedules(cron):
    with pytest.raises(ValidationError):
        ScheduleCreate(medicine_name="name", intake_period=cron, intake_finish=None, user_id=2)


async def test_negative_duration():
    with pytest.raises(ValidationError):
        ScheduleCreate(
            medicine_name="name",
            intake_period="*",
            intake_finish=intake_start - timedelta(days=1),
            intake_start=intake_start,
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
    Период приема таблеток с 8:00 - 22:00
    #"""  # noqa: RUF002

    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime(
                year=intake_start.year, month=intake_start.month, day=intake_start.day, hour=0, tzinfo=timezone.utc
            )

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
            return schedule.intake_finish + timedelta(days=1)

    monkeypatch.setattr("api.modules.schedule.datetime", MockDateTime)
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 400


async def test_constantly(schedule, client, monkeypatch, session):
    schedule.intake_finish = None
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200


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
async def test_next_takings(schedule, client, session, monkeypatch, schedules_count, days):
    class MockSettings:
        NEXT_TAKINGS_PERIOD = timedelta(days=days)

    monkeypatch.setattr("api.modules.schedule.manager.settings", MockSettings)

    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return intake_start

    monkeypatch.setattr("api.modules.schedule.manager.datetime", MockDateTime)

    session.add(schedule)
    await session.commit()

    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    response_json = response.json()
    assert len(response_json) == schedules_count
    for raw in response_json:
        scheduled = TakingsRead.model_validate(raw)
        assert_scheduled(scheduled.medicine_datetime)
