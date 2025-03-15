from datetime import datetime, timedelta, timezone

from crontab import CronTab
from fastapi_sqlalchemy_toolkit import ModelManager
from sqlmodel.ext.asyncio.session import AsyncSession

from ...conf import settings
from ...db import Schedule
from .schema import ScheduleCard, TakingsRead
from .utils import crontab_range


class ScheduleManager(ModelManager):
    def __init__(self, default_ordering=None):
        super().__init__(Schedule, default_ordering)

    def schedule(self, schedule_in: Schedule) -> list[ScheduleCard]:
        now = datetime.now(tz=timezone.utc)
        start = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=8,
            minute=0,
            second=0,
            microsecond=0,
        )
        stop = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=22,
            minute=0,
            second=0,
            microsecond=0,
        )
        scheduled = []
        for scheduled_datetime in self._generate_schedules_datetime(start, stop, schedule_in):
            scheduled.append(
                ScheduleCard.model_construct(
                    medicine_name=schedule_in.medicine_name, medicine_datetime=scheduled_datetime
                )
            )
        return scheduled

    @staticmethod
    def _generate_schedules_datetime(start: datetime, stop: datetime, schedule: Schedule):
        for scheduled_datetime in crontab_range(start=start, stop=stop, cron=CronTab(schedule.intake_period)):
            reminder = scheduled_datetime.minute % 15
            if scheduled_datetime.hour < 8 or scheduled_datetime.hour > 22:
                continue
            yield scheduled_datetime + timedelta(minutes=15 - reminder)

    async def next_takings(self, session: AsyncSession, user_id: str):
        start = datetime.now(tz=timezone.utc)
        stop = start + settings.NEXT_TAKINGS_PERIOD
        scheduled = []
        schedules = await self.list(session, user_id=user_id)
        for schedule in schedules:
            for scheduled_datetime in self._generate_schedules_datetime(start, stop, schedule):
                scheduled.append(
                    TakingsRead.model_construct(
                        medicine_name=schedule.medicine_name,
                        medicine_datetime=scheduled_datetime,
                        id=schedule.id,
                    )
                )
        return scheduled


schedule_manager = ScheduleManager()
