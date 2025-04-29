from datetime import datetime, timezone
from uuid import uuid4

from crontab import CronTab
from fastapi_sqlalchemy_toolkit import ModelManager
from sqlmodel.ext.asyncio.session import AsyncSession
from structlog import get_logger
from structlog.contextvars import bound_contextvars, get_contextvars

from ...conf import settings
from ...db import Schedule
from .schema import ScheduleCard, TakingsRead
from .utils import crontab_range

log = get_logger()


class ScheduleManager(ModelManager):
    def __init__(self, default_ordering=None):
        super().__init__(Schedule, default_ordering)

    def _schedule(self, schedule_in: Schedule):
        now = datetime.now(tz=timezone.utc)
        start = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=7,  # to have a 8:00 schedule
            minute=59,
            second=0,
            microsecond=0,
            tzinfo=timezone.utc,
        )
        stop = datetime(
            year=now.year, month=now.month, day=now.day, hour=22, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        expired_datetime = schedule_in.intake_finish if schedule_in.intake_finish else stop
        for scheduled_datetime in crontab_range(start, stop, CronTab(schedule_in.intake_period)):
            if scheduled_datetime > expired_datetime:
                return
            yield scheduled_datetime

    def schedule(self, schedule_in: Schedule) -> list[ScheduleCard]:
        scheduled = []
        for scheduled_datetime in self._schedule(schedule_in):
            scheduled.append(
                ScheduleCard.model_construct(
                    medicine_name=schedule_in.medicine_name, medicine_datetime=scheduled_datetime
                )
            )
        return scheduled

    async def _next_takings(self, session: AsyncSession, user_id: str):
        start = datetime.now(tz=timezone.utc)
        stop = start + settings.NEXT_TAKINGS_PERIOD
        schedules = await self.list(session, user_id=user_id)
        contextvars = get_contextvars()
        parent_span_id = contextvars["span_id"]
        with bound_contextvars(span_id=str(uuid4())):
            await log.ainfo("Sent request to db", parent_span_id=parent_span_id)
        for schedule in schedules:
            schedule: Schedule
            expired_datetime = schedule.intake_finish if schedule.intake_finish else stop
            for scheduled_datetime in crontab_range(start, stop, CronTab(schedule.intake_period)):
                if scheduled_datetime > expired_datetime:
                    break
                yield schedule, scheduled_datetime

    async def next_takings(self, session: AsyncSession, user_id: str):
        scheduled = []
        async for schedule, scheduled_datetime in self._next_takings(session, user_id):
            scheduled.append(
                TakingsRead.model_construct(
                    medicine_name=schedule.medicine_name,
                    medicine_datetime=scheduled_datetime,
                    id=schedule.id,
                )
            )
        return scheduled


schedule_manager = ScheduleManager()
