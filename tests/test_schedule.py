from datetime import time, timedelta
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time
from pydantic import ValidationError
from structlog.contextvars import bind_contextvars

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
def test_wrong_cron_syntax_schedules(cron):
    with pytest.raises(ValidationError):
        ScheduleCreate(medicine_name="name", intake_period=cron, intake_finish=None, user_id=2)


def test_finish_time_greater_then_start_time():
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
    "intake_period,intake_start,intake_finish, expected_schedules_datetime, schedule_lowest_bound,schedule_highest_bound",
    [
        (
            "15 20 * * *",
            day_with_zero_hour,
            None,
            [day_with_zero_hour.replace(hour=20, minute=15)],
            time(hour=8),
            time(hour=22),
        ),
        (
            "*/5 21 * * *",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=21, minute=00),
                day_with_zero_hour.replace(hour=21, minute=15),
                day_with_zero_hour.replace(hour=21, minute=30),
                day_with_zero_hour.replace(hour=21, minute=45),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=8, minute=00),
                day_with_zero_hour.replace(hour=9, minute=00),
                day_with_zero_hour.replace(hour=10, minute=00),
                day_with_zero_hour.replace(hour=11, minute=00),
                day_with_zero_hour.replace(hour=12, minute=00),
                day_with_zero_hour.replace(hour=13, minute=00),
                day_with_zero_hour.replace(hour=14, minute=00),
                day_with_zero_hour.replace(hour=15, minute=00),
                day_with_zero_hour.replace(hour=16, minute=00),
                day_with_zero_hour.replace(hour=17, minute=00),
                day_with_zero_hour.replace(hour=18, minute=00),
                day_with_zero_hour.replace(hour=19, minute=00),
                day_with_zero_hour.replace(hour=20, minute=00),
                day_with_zero_hour.replace(hour=21, minute=00),
                day_with_zero_hour.replace(hour=22, minute=00),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=6),
            day_with_zero_hour + timedelta(hours=8),
            [
                day_with_zero_hour.replace(hour=8, minute=0),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=22),
            day_with_zero_hour + timedelta(hours=23),
            [day_with_zero_hour.replace(hour=22, minute=00)],
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 9-15 * * *",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=9, minute=00),
                day_with_zero_hour.replace(hour=10, minute=00),
                day_with_zero_hour.replace(hour=11, minute=00),
                day_with_zero_hour.replace(hour=12, minute=00),
                day_with_zero_hour.replace(hour=13, minute=00),
                day_with_zero_hour.replace(hour=14, minute=00),
                day_with_zero_hour.replace(hour=15, minute=00),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=10),
            day_with_zero_hour + timedelta(hours=23),
            [
                day_with_zero_hour.replace(hour=10, minute=00),
                day_with_zero_hour.replace(hour=11, minute=00),
                day_with_zero_hour.replace(hour=12, minute=00),
                day_with_zero_hour.replace(hour=13, minute=00),
                day_with_zero_hour.replace(hour=14, minute=00),
                day_with_zero_hour.replace(hour=15, minute=00),
                day_with_zero_hour.replace(hour=16, minute=00),
                day_with_zero_hour.replace(hour=17, minute=00),
                day_with_zero_hour.replace(hour=18, minute=00),
                day_with_zero_hour.replace(hour=19, minute=00),
                day_with_zero_hour.replace(hour=20, minute=00),
                day_with_zero_hour.replace(hour=21, minute=00),
                day_with_zero_hour.replace(hour=22, minute=00),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 * * * *",
            day_with_zero_hour + timedelta(hours=20),
            day_with_zero_hour + timedelta(hours=23),
            [
                day_with_zero_hour.replace(hour=20, minute=00),
                day_with_zero_hour.replace(hour=21, minute=00),
                day_with_zero_hour.replace(hour=22, minute=00),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            # schedule on the next day
            f"0 * {(day_with_zero_hour + timedelta(days=1)).day} * *",
            day_with_zero_hour,
            None,
            [],
            time(hour=8),
            time(hour=22),
        ),
        (
            "7 11-15 * * *",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=11, minute=15),
                day_with_zero_hour.replace(hour=12, minute=15),
                day_with_zero_hour.replace(hour=13, minute=15),
                day_with_zero_hour.replace(hour=14, minute=15),
                day_with_zero_hour.replace(hour=15, minute=15),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "7 11-15 * * *",
            day_with_zero_hour,
            day_with_zero_hour + timedelta(hours=14),
            [
                day_with_zero_hour.replace(hour=11, minute=15),
                day_with_zero_hour.replace(hour=12, minute=15),
                day_with_zero_hour.replace(hour=13, minute=15),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "*/50 * * * *",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=8, minute=0),
                day_with_zero_hour.replace(hour=9, minute=0),
                day_with_zero_hour.replace(hour=10, minute=0),
                day_with_zero_hour.replace(hour=11, minute=0),
                day_with_zero_hour.replace(hour=12, minute=0),
                day_with_zero_hour.replace(hour=13, minute=0),
                day_with_zero_hour.replace(hour=14, minute=0),
                day_with_zero_hour.replace(hour=15, minute=0),
                day_with_zero_hour.replace(hour=16, minute=0),
                day_with_zero_hour.replace(hour=17, minute=0),
                day_with_zero_hour.replace(hour=18, minute=0),
                day_with_zero_hour.replace(hour=19, minute=0),
                day_with_zero_hour.replace(hour=20, minute=0),
                day_with_zero_hour.replace(hour=21, minute=0),
                day_with_zero_hour.replace(hour=22, minute=0),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            f"*/50 * {day_with_zero_hour.day} {day_with_zero_hour.month} {day_with_zero_hour.weekday() + 1},5",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=8, minute=0),
                day_with_zero_hour.replace(hour=9, minute=0),
                day_with_zero_hour.replace(hour=10, minute=0),
                day_with_zero_hour.replace(hour=11, minute=0),
                day_with_zero_hour.replace(hour=12, minute=0),
                day_with_zero_hour.replace(hour=13, minute=0),
                day_with_zero_hour.replace(hour=14, minute=0),
                day_with_zero_hour.replace(hour=15, minute=0),
                day_with_zero_hour.replace(hour=16, minute=0),
                day_with_zero_hour.replace(hour=17, minute=0),
                day_with_zero_hour.replace(hour=18, minute=0),
                day_with_zero_hour.replace(hour=19, minute=0),
                day_with_zero_hour.replace(hour=20, minute=0),
                day_with_zero_hour.replace(hour=21, minute=0),
                day_with_zero_hour.replace(hour=22, minute=0),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            f"*/50 * {day_with_zero_hour.day}-15 {day_with_zero_hour.month}-10,11 {day_with_zero_hour.weekday() + 1},5",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=8, minute=0),
                day_with_zero_hour.replace(hour=9, minute=0),
                day_with_zero_hour.replace(hour=10, minute=0),
                day_with_zero_hour.replace(hour=11, minute=0),
                day_with_zero_hour.replace(hour=12, minute=0),
                day_with_zero_hour.replace(hour=13, minute=0),
                day_with_zero_hour.replace(hour=14, minute=0),
                day_with_zero_hour.replace(hour=15, minute=0),
                day_with_zero_hour.replace(hour=16, minute=0),
                day_with_zero_hour.replace(hour=17, minute=0),
                day_with_zero_hour.replace(hour=18, minute=0),
                day_with_zero_hour.replace(hour=19, minute=0),
                day_with_zero_hour.replace(hour=20, minute=0),
                day_with_zero_hour.replace(hour=21, minute=0),
                day_with_zero_hour.replace(hour=22, minute=0),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            f"*/50 * {day_with_zero_hour.day} {day_with_zero_hour.month} {day_with_zero_hour.weekday() + 1}",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=8, minute=0),
                day_with_zero_hour.replace(hour=9, minute=0),
                day_with_zero_hour.replace(hour=10, minute=0),
                day_with_zero_hour.replace(hour=11, minute=0),
                day_with_zero_hour.replace(hour=12, minute=0),
                day_with_zero_hour.replace(hour=13, minute=0),
                day_with_zero_hour.replace(hour=14, minute=0),
                day_with_zero_hour.replace(hour=15, minute=0),
                day_with_zero_hour.replace(hour=16, minute=0),
                day_with_zero_hour.replace(hour=17, minute=0),
                day_with_zero_hour.replace(hour=18, minute=0),
                day_with_zero_hour.replace(hour=19, minute=0),
                day_with_zero_hour.replace(hour=20, minute=0),
                day_with_zero_hour.replace(hour=21, minute=0),
                day_with_zero_hour.replace(hour=22, minute=0),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "0 10,20 * * *",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=10, minute=0),
                day_with_zero_hour.replace(hour=20, minute=0),
            ],
            time(hour=8),
            time(hour=22),
        ),
        (
            "10 */8 * * *",
            day_with_zero_hour,
            None,
            [
                day_with_zero_hour.replace(hour=8, minute=15),
                day_with_zero_hour.replace(hour=16, minute=15),
            ],
            time(hour=8),
            time(hour=22),
        ),
    ],
)
def test_schedule(
    intake_period,
    intake_start,
    intake_finish,
    expected_schedules_datetime,
    schedule_lowest_bound,
    schedule_highest_bound,
):
    """
    Тестирование алгоритма выдачи приема таблеток на день с 8:00 - до 22:00
    """  # noqa: RUF002

    schedule_db = Schedule(
        medicine_name="", user_id=1, intake_period=intake_period, intake_finish=intake_finish, intake_start=intake_start
    )
    schedule_repo = ScheduleRepo(AsyncMock(), schedule_lowest_bound, schedule_highest_bound)
    schedule_and_scheduled_datetime = list(schedule_repo.schedule(schedule_db))
    assert len(schedule_and_scheduled_datetime) == len(expected_schedules_datetime)
    for scheduled_datetime, expected_datetime in zip(schedule_and_scheduled_datetime, expected_schedules_datetime):
        assert scheduled_datetime[1] == expected_datetime


@pytest.mark.anyio
@freeze_time(day_with_zero_hour)
@pytest.mark.parametrize(
    "schedules, start, stop, expected_schedules_datetime, schedule_lowest_bound,schedule_highest_bound",
    [
        (
            [
                Schedule(
                    medicine_name="",
                    user_id=1,
                    intake_period="0 12 * * *",
                    intake_start=day_with_zero_hour,
                    intake_finish=None,
                ),
            ],
            day_with_zero_hour - timedelta(days=3),
            day_with_zero_hour + timedelta(days=3),
            [
                day_with_zero_hour.replace(hour=12),
                day_with_zero_hour.replace(hour=12) + timedelta(days=1),
                day_with_zero_hour.replace(hour=12) + timedelta(days=2),
            ],
            time(hour=8),
            time(hour=22),
        )
    ],
)
async def test_next_takings(
    schedules, start, stop, expected_schedules_datetime, schedule_lowest_bound, schedule_highest_bound
):
    bind_contextvars(span_id=1)
    mock_session = AsyncMock()
    mock_session.exec.return_value = schedules
    schedule_repo = ScheduleRepo(mock_session, schedule_lowest_bound, schedule_highest_bound)

    schedule_and_scheduled_datetime = [schedules async for schedules in schedule_repo.next_takings(0, start, stop)]
    assert len(schedule_and_scheduled_datetime) == len(expected_schedules_datetime)
    for scheduled_datetime, expected_datetime in zip(schedule_and_scheduled_datetime, expected_schedules_datetime):
        assert scheduled_datetime[1] == expected_datetime
