from datetime import timedelta

import pytest
from pydantic import ValidationError

from src.api.schemas.schedule_schema import ScheduleCreate

from .utils import intake_start


@pytest.mark.parametrize(
    "cron",
    [
        "23",  # intake period in 8 or 22 hours
        "24",
        "7",
        "5",
    ],
)
def test_wrong_schedules(cron):
    with pytest.raises(ValidationError):
        ScheduleCreate(medicine_name="name", intake_period=cron, intake_finish=None, user_id=2)


def test_negative_duration():
    with pytest.raises(ValidationError):
        ScheduleCreate(
            medicine_name="name",
            intake_period="*",
            intake_finish=intake_start - timedelta(days=1),
            intake_start=intake_start,
            user_id=2,
        )
