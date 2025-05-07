from datetime import time, timedelta
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time
from pydantic import ValidationError

from src.api.schemas.schedules import ScheduleCreate
from src.db.schedules import Schedule
from src.integrations.schedules_repo import ScheduleRepo
from tests.utils import day_with_zero_hour


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
            intake_finish=day_with_zero_hour - timedelta(days=1),
            intake_start=day_with_zero_hour,
            user_id=2,
        )


@freeze_time(day_with_zero_hour)
@pytest.mark.parametrize(
    "intake_period,intake_start,intake_finish,schedules_count,schedule_lowest_bound,schedule_highest_bound",
    [
        (
            "15 20 * * *",
            day_with_zero_hour,
            None,
            1,  # 20:15
            time(hour=8),
            time(hour=22),
        ),
        (
            "*/5 21 * * *",
            day_with_zero_hour,
            None,
            3,  # 21:15 21:30 21:45
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour,
            None,
            14,  # 8:15 9:15 .... 20:15 21:15
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=6),
            day_with_zero_hour + timedelta(hours=8),
            1,  # 8:00
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=22),
            day_with_zero_hour + timedelta(hours=23),
            1,  # 22:00
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 9-15 * * *",
            day_with_zero_hour,
            None,
            7,  # 9:00 10:00 11:00 12:00 13:00 14:00 15:00
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=10),
            day_with_zero_hour + timedelta(hours=23),
            12,
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=20),
            day_with_zero_hour + timedelta(hours=23),
            3,  # 20:00 21:00 22:00
            time(hour=8),
            time(hour=22),
        ),
        (
            f"0 * {(day_with_zero_hour + timedelta(days=1)).day} * *",
            day_with_zero_hour,
            None,
            0,
            time(hour=8),
            time(hour=22),
        ),
    ],
)
def test_schedule(
    intake_period, intake_start, intake_finish, schedules_count, schedule_lowest_bound, schedule_highest_bound
):
    """
    Тестирование алгоритма выдачи приема таблеток на день с 8:00 - до 22:00
    """  # noqa: RUF002

    schedule = Schedule(
        medicine_name="", user_id=1, intake_period=intake_period, intake_finish=intake_finish, intake_start=intake_start
    )
    schedule_repo = ScheduleRepo(AsyncMock(), schedule_lowest_bound, schedule_highest_bound)
    assert len(list(schedule_repo.schedule(schedule))) == schedules_count
