from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from crontab import CronTab
from sqlalchemy.exc import MultipleResultsFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from structlog import get_logger

from src.api.schemas.schema import ScheduleCard
from src.db import Schedule

log = get_logger()


class IScheduleService(ABC):
    def __init__(self, session: AsyncSession):
        self._session = session
        super().__init__()

    @staticmethod
    def crontab_range(start: datetime, stop: datetime, cron: CronTab):
        while True:
            start = cron.next(now=start, return_datetime=True, default_utc=True)
            reminder = start.minute % 15
            if reminder != 0 or start.minute == 0:
                start += timedelta(minutes=15 - reminder)
            if start > stop:
                break
            if start == stop:
                yield start
                break
            if start.hour < 8 or start.hour > 22:
                continue
            if start.hour == 22 and start.minute != 0:
                continue
            yield start

    def schedule(self, schedule_in: Schedule):
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
        results = []
        for scheduled_datetime in self.crontab_range(start, stop, CronTab(schedule_in.intake_period)):
            if scheduled_datetime > expired_datetime:
                return
            results.append(self.view(schedule_in, scheduled_datetime))

        return results

    @abstractmethod
    def view(self, schedule_in: Schedule, scheduled_datetime):
        pass

    async def get(self, user_id: int, schedule_id: int):
        try:
            result = await self._session.exec(
                select(Schedule).where((Schedule.user_id == user_id) & (Schedule.id == schedule_id))
            )
            return result.one_or_none()
        except MultipleResultsFound:
            await log.awarning("Multiple results returned from get schedule", schedule_id=schedule_id, user_id=user_id)
            return result.first()


class ScheduleServiceHTTP(IScheduleService):
    def view(self, schedule_in, scheduled_datetime):
        return ScheduleCard.model_construct(
            medicine_name=schedule_in.medicine_name, medicine_datetime=scheduled_datetime
        )
