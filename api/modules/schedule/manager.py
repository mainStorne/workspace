from datetime import datetime, timedelta, timezone

from crontab import CronTab
from fastapi_sqlalchemy_toolkit import ModelManager

from ...db import Schedule
from .schema import ScheduleCard
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
        for scheduled_datetime in crontab_range(start=start, stop=stop, cron=CronTab(schedule_in.intake_period)):
            # TODO write tests
            reminder = scheduled_datetime.minute % 15
            scheduled.append(
                ScheduleCard.model_construct(
                    medicine_name=schedule_in.medicine_name,
                    medicine_datetime=scheduled_datetime + timedelta(minutes=15 - reminder),
                )
            )
        return scheduled


schedule_manager = ScheduleManager()
