from datetime import timedelta

import pytest
from pydantic import ValidationError

from api.db import Schedule
from api.modules.schedule.schema import ScheduleCard, ScheduleCreate, TakingsRead

pytestmark = pytest.mark.anyio


async def test_create_schedule(client, session):
    with pytest.raises(ValidationError):
        ScheduleCreate(medicine_name="", intake_period="44214", treatment_duration=timedelta(days=5), user_id="42")

    schedule = ScheduleCreate(
        medicine_name="name", intake_period="0 12 * * *", treatment_duration=timedelta(days=5), user_id="543423"
    )

    response = await client.post("/schedule", content=schedule.model_dump_json())
    assert response.status_code == 200
    schedule_id = response.json()["id"]
    schedule = await session.get(Schedule, schedule_id)
    assert schedule is not None

    schedule = ScheduleCreate(
        medicine_name="name", intake_period="0 12 * * *", treatment_duration=None, user_id="543423"
    )

    response = await client.post("/schedule", content=schedule.model_dump_json())
    assert response.status_code == 200
    schedule_id = response.json()["id"]
    schedule = await session.get(Schedule, schedule_id)
    assert schedule is not None


async def test_schedule_period(schedule, client, session):
    """
    Пириод приема таблетков с 8:00 - 22:00
    """  # noqa: RUF002
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200
    for raw in response.json():
        scheduled = ScheduleCard.model_validate(raw)
        assert 8 <= scheduled.medicine_datetime.hour <= 22
        assert scheduled.medicine_datetime.minute % 15 == 0

    schedule.intake_period = "15 22 * * *"
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200
    assert response.json() == []

    # run every 5 minute
    schedule.intake_period = "*/5 14 * * *"
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200
    for raw in response.json():
        scheduled = ScheduleCard.model_validate(raw)
        assert 8 <= scheduled.medicine_datetime.hour <= 22
        assert scheduled.medicine_datetime.minute % 15 == 0


async def test_expired_medicine_datetime(schedule, client, monkeypatch):
    class MockDateTime:
        @classmethod
        def now(cls, tz=None):
            return schedule.schedule_datetime + schedule.treatment_duration + timedelta(days=1)

    monkeypatch.setattr("api.modules.schedule.datetime", MockDateTime)
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 400


async def test_constantly_medicine_datetime(schedule, client, monkeypatch, session):
    schedule.treatment_duration = None
    session.add(schedule)
    await session.commit()
    response = await client.get("/schedule", params={"user_id": schedule.user_id, "schedule_id": schedule.id})
    assert response.status_code == 200


async def test_next_takings(schedule, client, session, monkeypatch):
    class MockSettings:
        NEXT_TAKINGS_PERIOD = timedelta(days=1)

    monkeypatch.setattr("api.modules.schedule.manager.settings", MockSettings)
    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    TakingsRead.model_validate(response_json[0])

    schedule_2 = Schedule(
        medicine_name="test2",
        intake_period="10 */6 * * *",
        treatment_duration=None,
        user_id=schedule.user_id,
    )
    session.add(schedule_2)
    await session.commit()

    response = await client.get("/next_takings", params={"user_id": schedule.user_id})
    response_json = response.json()
    for raw in response_json:
        scheduled = TakingsRead.model_validate(raw)
        assert 8 <= scheduled.medicine_datetime.hour <= 22
        assert scheduled.medicine_datetime.minute % 15 == 0
