from datetime import datetime, timezone

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
            hour=7,  # to have a 8:00 schedule
            minute=59,
            second=0,
            microsecond=0,
            tzinfo=timezone.utc,
        )
        stop = datetime(
            year=now.year, month=now.month, day=now.day, hour=22, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        expired_datetime = (
            schedule_in.schedule_datetime + schedule_in.treatment_duration if schedule_in.treatment_duration else stop
        )
        scheduled = []
        for scheduled_datetime in crontab_range(start, stop, CronTab(schedule_in.intake_period)):
            if scheduled_datetime > expired_datetime:
                break
            scheduled.append(
                ScheduleCard.model_construct(
                    medicine_name=schedule_in.medicine_name, medicine_datetime=scheduled_datetime
                )
            )
        return scheduled

    async def next_takings(self, session: AsyncSession, user_id: str):
        start = datetime.now(tz=timezone.utc)
        stop = start + settings.NEXT_TAKINGS_PERIOD
        scheduled = []
        schedules = await self.list(session, user_id=user_id)
        for schedule in schedules:
            schedule: Schedule
            expired_datetime = (
                schedule.schedule_datetime + schedule.treatment_duration if schedule.treatment_duration else stop
            )
            for scheduled_datetime in crontab_range(start, stop, CronTab(schedule.intake_period)):
                if scheduled_datetime > expired_datetime:
                    break
                scheduled.append(
                    TakingsRead.model_construct(
                        medicine_name=schedule.medicine_name,
                        medicine_datetime=scheduled_datetime,
                        id=schedule.id,
                    )
                )
        return scheduled


schedule_manager = ScheduleManager()
