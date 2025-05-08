from datetime import time, timedelta
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time
from pydantic import ValidationError
from structlog.contextvars import bind_contextvars

from src.api.schemas.schedules import ScheduleCreate
from src.db.schedules import Schedule
from src.integrations.schedules_repo import ScheduleRepo
from tests.utils import zero_day_fixture


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
            intake_finish=zero_day_fixture - timedelta(days=1),
            intake_start=zero_day_fixture,
            user_id=2,
        )


@freeze_time(zero_day_fixture)
@pytest.mark.parametrize(
    "intake_period,intake_start,intake_finish, expected_schedules_datetime",
    [
        (
            "15 20 * * *",
            zero_day_fixture,
            None,
            [zero_day_fixture.replace(hour=20, minute=15)],
        ),
        (
            "*/5 21 * * *",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=21, minute=00),
                zero_day_fixture.replace(hour=21, minute=15),
                zero_day_fixture.replace(hour=21, minute=30),
                zero_day_fixture.replace(hour=21, minute=45),
            ],
        ),
        (
            "0 * * * *",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=8, minute=00),
                zero_day_fixture.replace(hour=9, minute=00),
                zero_day_fixture.replace(hour=10, minute=00),
                zero_day_fixture.replace(hour=11, minute=00),
                zero_day_fixture.replace(hour=12, minute=00),
                zero_day_fixture.replace(hour=13, minute=00),
                zero_day_fixture.replace(hour=14, minute=00),
                zero_day_fixture.replace(hour=15, minute=00),
                zero_day_fixture.replace(hour=16, minute=00),
                zero_day_fixture.replace(hour=17, minute=00),
                zero_day_fixture.replace(hour=18, minute=00),
                zero_day_fixture.replace(hour=19, minute=00),
                zero_day_fixture.replace(hour=20, minute=00),
                zero_day_fixture.replace(hour=21, minute=00),
                zero_day_fixture.replace(hour=22, minute=00),
            ],
        ),
        (
            "0 * * * *",
            zero_day_fixture + timedelta(hours=6),
            zero_day_fixture + timedelta(hours=8),
            [
                zero_day_fixture.replace(hour=8, minute=0),
            ],
        ),
        (
            "0 * * * *",
            zero_day_fixture + timedelta(hours=22),
            zero_day_fixture + timedelta(hours=23),
            [zero_day_fixture.replace(hour=22, minute=00)],
        ),
        (
            "0 9-15 * * *",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=9, minute=00),
                zero_day_fixture.replace(hour=10, minute=00),
                zero_day_fixture.replace(hour=11, minute=00),
                zero_day_fixture.replace(hour=12, minute=00),
                zero_day_fixture.replace(hour=13, minute=00),
                zero_day_fixture.replace(hour=14, minute=00),
                zero_day_fixture.replace(hour=15, minute=00),
            ],
        ),
        (
            "0 * * * *",
            zero_day_fixture + timedelta(hours=10),
            zero_day_fixture + timedelta(hours=23),
            [
                zero_day_fixture.replace(hour=10, minute=00),
                zero_day_fixture.replace(hour=11, minute=00),
                zero_day_fixture.replace(hour=12, minute=00),
                zero_day_fixture.replace(hour=13, minute=00),
                zero_day_fixture.replace(hour=14, minute=00),
                zero_day_fixture.replace(hour=15, minute=00),
                zero_day_fixture.replace(hour=16, minute=00),
                zero_day_fixture.replace(hour=17, minute=00),
                zero_day_fixture.replace(hour=18, minute=00),
                zero_day_fixture.replace(hour=19, minute=00),
                zero_day_fixture.replace(hour=20, minute=00),
                zero_day_fixture.replace(hour=21, minute=00),
                zero_day_fixture.replace(hour=22, minute=00),
            ],
        ),
        (
            "0 * * * *",
            zero_day_fixture + timedelta(hours=20),
            zero_day_fixture + timedelta(hours=23),
            [
                zero_day_fixture.replace(hour=20, minute=00),
                zero_day_fixture.replace(hour=21, minute=00),
                zero_day_fixture.replace(hour=22, minute=00),
            ],
        ),
        (
            # schedule on the next day
            f"0 * {(zero_day_fixture + timedelta(days=1)).day} * *",
            zero_day_fixture,
            None,
            [],
        ),
        (
            "7 11-15 * * *",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=11, minute=15),
                zero_day_fixture.replace(hour=12, minute=15),
                zero_day_fixture.replace(hour=13, minute=15),
                zero_day_fixture.replace(hour=14, minute=15),
                zero_day_fixture.replace(hour=15, minute=15),
            ],
        ),
        (
            "7 11-15 * * *",
            zero_day_fixture,
            zero_day_fixture + timedelta(hours=14),
            [
                zero_day_fixture.replace(hour=11, minute=15),
                zero_day_fixture.replace(hour=12, minute=15),
                zero_day_fixture.replace(hour=13, minute=15),
            ],
        ),
        (
            "*/50 * * * *",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=8, minute=0),
                zero_day_fixture.replace(hour=9, minute=0),
                zero_day_fixture.replace(hour=10, minute=0),
                zero_day_fixture.replace(hour=11, minute=0),
                zero_day_fixture.replace(hour=12, minute=0),
                zero_day_fixture.replace(hour=13, minute=0),
                zero_day_fixture.replace(hour=14, minute=0),
                zero_day_fixture.replace(hour=15, minute=0),
                zero_day_fixture.replace(hour=16, minute=0),
                zero_day_fixture.replace(hour=17, minute=0),
                zero_day_fixture.replace(hour=18, minute=0),
                zero_day_fixture.replace(hour=19, minute=0),
                zero_day_fixture.replace(hour=20, minute=0),
                zero_day_fixture.replace(hour=21, minute=0),
                zero_day_fixture.replace(hour=22, minute=0),
            ],
        ),
        (
            f"*/50 * {zero_day_fixture.day} {zero_day_fixture.month} {zero_day_fixture.weekday() + 1},5",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=8, minute=0),
                zero_day_fixture.replace(hour=9, minute=0),
                zero_day_fixture.replace(hour=10, minute=0),
                zero_day_fixture.replace(hour=11, minute=0),
                zero_day_fixture.replace(hour=12, minute=0),
                zero_day_fixture.replace(hour=13, minute=0),
                zero_day_fixture.replace(hour=14, minute=0),
                zero_day_fixture.replace(hour=15, minute=0),
                zero_day_fixture.replace(hour=16, minute=0),
                zero_day_fixture.replace(hour=17, minute=0),
                zero_day_fixture.replace(hour=18, minute=0),
                zero_day_fixture.replace(hour=19, minute=0),
                zero_day_fixture.replace(hour=20, minute=0),
                zero_day_fixture.replace(hour=21, minute=0),
                zero_day_fixture.replace(hour=22, minute=0),
            ],
        ),
        (
            f"*/50 * {zero_day_fixture.day}-15 {zero_day_fixture.month}-10,11 {zero_day_fixture.weekday() + 1},5",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=8, minute=0),
                zero_day_fixture.replace(hour=9, minute=0),
                zero_day_fixture.replace(hour=10, minute=0),
                zero_day_fixture.replace(hour=11, minute=0),
                zero_day_fixture.replace(hour=12, minute=0),
                zero_day_fixture.replace(hour=13, minute=0),
                zero_day_fixture.replace(hour=14, minute=0),
                zero_day_fixture.replace(hour=15, minute=0),
                zero_day_fixture.replace(hour=16, minute=0),
                zero_day_fixture.replace(hour=17, minute=0),
                zero_day_fixture.replace(hour=18, minute=0),
                zero_day_fixture.replace(hour=19, minute=0),
                zero_day_fixture.replace(hour=20, minute=0),
                zero_day_fixture.replace(hour=21, minute=0),
                zero_day_fixture.replace(hour=22, minute=0),
            ],
        ),
        (
            f"*/50 * {zero_day_fixture.day} {zero_day_fixture.month} {zero_day_fixture.weekday() + 1}",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=8, minute=0),
                zero_day_fixture.replace(hour=9, minute=0),
                zero_day_fixture.replace(hour=10, minute=0),
                zero_day_fixture.replace(hour=11, minute=0),
                zero_day_fixture.replace(hour=12, minute=0),
                zero_day_fixture.replace(hour=13, minute=0),
                zero_day_fixture.replace(hour=14, minute=0),
                zero_day_fixture.replace(hour=15, minute=0),
                zero_day_fixture.replace(hour=16, minute=0),
                zero_day_fixture.replace(hour=17, minute=0),
                zero_day_fixture.replace(hour=18, minute=0),
                zero_day_fixture.replace(hour=19, minute=0),
                zero_day_fixture.replace(hour=20, minute=0),
                zero_day_fixture.replace(hour=21, minute=0),
                zero_day_fixture.replace(hour=22, minute=0),
            ],
        ),
        (
            "0 10,20 * * *",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=10, minute=0),
                zero_day_fixture.replace(hour=20, minute=0),
            ],
        ),
        (
            "10 */8 * * *",
            zero_day_fixture,
            None,
            [
                zero_day_fixture.replace(hour=8, minute=15),
                zero_day_fixture.replace(hour=16, minute=15),
            ],
        ),
    ],
)
def test_schedule(
    intake_period,
    intake_start,
    intake_finish,
    expected_schedules_datetime,
):
    """
    Тестирование алгоритма выдачи приема таблеток на день с 8:00 - до 22:00
    """  # noqa: RUF002

    schedule_db = Schedule(
        medicine_name="", user_id=1, intake_period=intake_period, intake_finish=intake_finish, intake_start=intake_start
    )
    schedule_repo = ScheduleRepo(AsyncMock(), time(hour=8), time(hour=22))
    schedule_and_scheduled_datetime = list(schedule_repo.schedule(schedule_db))
    assert len(schedule_and_scheduled_datetime) == len(expected_schedules_datetime)
    for scheduled_datetime, expected_datetime in zip(schedule_and_scheduled_datetime, expected_schedules_datetime):
        assert scheduled_datetime[1] == expected_datetime


@freeze_time(zero_day_fixture)
@pytest.mark.anyio
@pytest.mark.parametrize(
    "start_datetime, stop_datetime, expected",
    [
        (
            zero_day_fixture - timedelta(days=3),
            zero_day_fixture + timedelta(days=3),
            [
                (0, zero_day_fixture + timedelta(hours=12)),
                (0, zero_day_fixture + timedelta(days=1, hours=12)),
                (0, zero_day_fixture + timedelta(days=2, hours=12)),
                (1, zero_day_fixture - timedelta(days=1) + timedelta(hours=9, minutes=15)),
                (1, zero_day_fixture - timedelta(days=1) + timedelta(hours=18, minutes=15)),
                (1, zero_day_fixture + timedelta(hours=9, minutes=15)),
                (1, zero_day_fixture + timedelta(hours=18, minutes=15)),
                (1, zero_day_fixture + timedelta(days=1, hours=9, minutes=15)),
                (1, zero_day_fixture + timedelta(days=1, hours=18, minutes=15)),
                (1, zero_day_fixture + timedelta(days=2, hours=9, minutes=15)),
                (1, zero_day_fixture + timedelta(days=2, hours=18, minutes=15)),
                (2, zero_day_fixture + timedelta(days=2, hours=8)),
                (2, zero_day_fixture + timedelta(days=2, hours=14)),
                (2, zero_day_fixture + timedelta(days=2, hours=18)),
            ],
        ),
    ],
)
async def test_next_takings(start_datetime, stop_datetime, expected):
    bind_contextvars(span_id=1)
    mock_session = AsyncMock()
    schedule_fixture = [
        Schedule(
            medicine_name="0",
            user_id=1,
            intake_period="0 12 * * *",
            intake_start=zero_day_fixture,
            intake_finish=zero_day_fixture + timedelta(days=5, hours=12),
        ),
        Schedule(
            medicine_name="1",
            user_id=1,
            intake_period="15 9,18 * * *",
            intake_start=zero_day_fixture - timedelta(days=1),
            intake_finish=None,
        ),
        Schedule(
            medicine_name="2",
            user_id=1,
            intake_period="0 8,14,18 */7 * *",
            intake_start=zero_day_fixture,
            intake_finish=zero_day_fixture + timedelta(days=30),
        ),
    ]
    mock_session.exec.return_value = schedule_fixture
    schedule_repo = ScheduleRepo(mock_session, time(hour=8), time(hour=22))

    next_takings = [schedules async for schedules in schedule_repo.next_takings(0, start_datetime, stop=stop_datetime)]
    assert len(next_takings) == len(expected)
    for (schedule, scheduled_datetime), (schedule_idx, expected_datetime) in zip(next_takings, expected):
        assert scheduled_datetime == expected_datetime
        assert schedule == schedule_fixture[schedule_idx]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "start_datetime, stop_datetime, expected",
    [
        (
            zero_day_fixture + timedelta(days=1),
            zero_day_fixture + timedelta(days=8),
            [
                zero_day_fixture + timedelta(days=1, hours=12),
                zero_day_fixture + timedelta(days=2, hours=12),
                zero_day_fixture + timedelta(days=3, hours=12),
                zero_day_fixture + timedelta(days=4, hours=12),
                zero_day_fixture + timedelta(days=5, hours=12),
            ],
        ),
    ],
)
async def test_next_takings_bound_values(start_datetime, stop_datetime, expected):
    schedule_fixture = [
        Schedule(
            medicine_name="",
            user_id=1,
            intake_period="0 12 * * *",
            intake_start=zero_day_fixture,
            intake_finish=zero_day_fixture + timedelta(days=5, hours=12),
        ),
        Schedule(  # filtered out with schedule_lowest_bound
            medicine_name="1",
            user_id=1,
            intake_period="0 6 * * *",
            intake_start=zero_day_fixture + timedelta(days=1),
            intake_finish=zero_day_fixture + timedelta(days=4),
        ),
    ]
    bind_contextvars(span_id=1)
    mock_session = AsyncMock()
    mock_session.exec.return_value = schedule_fixture
    schedule_repo = ScheduleRepo(mock_session, time(hour=8), time(hour=22))

    next_takings = [schedules async for schedules in schedule_repo.next_takings(0, start_datetime, stop=stop_datetime)]
    assert len(next_takings) == len(expected)
    for (schedule, scheduled_datetime), expected_datetime in zip(next_takings, expected):
        assert scheduled_datetime == expected_datetime
        assert schedule == schedule_fixture[0]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "start_datetime, stop_datetime, expected",
    [
        (
            zero_day_fixture + timedelta(days=1),
            zero_day_fixture + timedelta(days=8),
            [
                (0, zero_day_fixture + timedelta(days=1, hours=12)),
                (0, zero_day_fixture + timedelta(days=2, hours=12)),
                (0, zero_day_fixture + timedelta(days=3, hours=12)),
                (0, zero_day_fixture + timedelta(days=4, hours=12)),
                (0, zero_day_fixture + timedelta(days=5, hours=12)),
                (1, zero_day_fixture + timedelta(days=1, hours=12)),
                (1, zero_day_fixture + timedelta(days=2, hours=12)),
                (1, zero_day_fixture + timedelta(days=3, hours=12)),
                (1, zero_day_fixture + timedelta(days=4, hours=12)),
                (1, zero_day_fixture + timedelta(days=5, hours=12)),
            ],
        )
    ],
)
async def test_next_takings_overlap_schedules(start_datetime, stop_datetime, expected):
    schedule_fixture = [
        Schedule(
            medicine_name="0",
            user_id=1,
            intake_period="0 12 * * *",
            intake_start=zero_day_fixture,
            intake_finish=zero_day_fixture + timedelta(days=5, hours=12),
        ),
        Schedule(
            medicine_name="1",
            user_id=1,
            intake_period="0 12 * * *",
            intake_start=zero_day_fixture,
            intake_finish=zero_day_fixture + timedelta(days=5, hours=12),
        ),
    ]

    bind_contextvars(span_id=1)
    mock_session = AsyncMock()
    mock_session.exec.return_value = schedule_fixture
    schedule_repo = ScheduleRepo(mock_session, time(hour=8), time(hour=22))

    next_takings = [schedules async for schedules in schedule_repo.next_takings(0, start_datetime, stop=stop_datetime)]
    assert len(next_takings) == len(expected)
    for (schedule, scheduled_datetime), (schedule_idx, expected_datetime) in zip(next_takings, expected):
        assert scheduled_datetime == expected_datetime
        assert schedule == schedule_fixture[schedule_idx]
