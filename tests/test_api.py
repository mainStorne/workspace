from datetime import timedelta

import pytest
from pydantic import ValidationError

from api.db import Schedule
from api.modules.schedule.schema import ScheduleCreate

pytestmark = pytest.mark.anyio


async def test_schedule(client, session):
    with pytest.raises(ValidationError):
        ScheduleCreate(medicine_name="", intake_period="44214", treatment_duration=timedelta(days=5), user_id="42")

    schedule = ScheduleCreate(
        medicine_name="name", intake_period="0 12 * * *", treatment_duration=timedelta(days=5), user_id="543423"
    )

    response = await client.post("/schedule", content=schedule.model_dump_json())
    assert response.status_code == 200
    schedule_id = response.json()["schedule_id"]
    schedule = await session.get(Schedule, schedule_id)
    assert schedule is not None
