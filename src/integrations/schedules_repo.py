from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

from crontab import CronTab
from sqlalchemy.exc import MultipleResultsFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from structlog import get_logger
from structlog.contextvars import bound_contextvars, get_contextvars

from src.api.schemas.schedules import ScheduleCreate
from src.db import Schedule

log = get_logger()


class IScheduleRepo(ABC):
    def __init__(self, session: AsyncSession, schedule_lowest_bound: time, schedule_highest_bound: time):
        self._session = session
        self._schedule_lowest_bound = schedule_lowest_bound
        self._schedule_highest_bound = schedule_highest_bound
        super().__init__()

    @abstractmethod
    def schedule(self, schedule_in: Schedule): ...
    @abstractmethod
    async def get(self, user_id: int, schedule_id: int): ...

    @abstractmethod
    async def next_takings(self, user_id: int, start: datetime, stop: datetime): ...

    @abstractmethod
    async def schedules(self, user_id: int) -> Iterable[Schedule]: ...

    @abstractmethod
    async def create(self, schedule: ScheduleCreate): ...


class ScheduleRepo(IScheduleRepo):
    @staticmethod
    def _round_time_by_15(time_to_round: time):
        reminder = time_to_round.minute % 15
        if reminder != 0 or time_to_round.minute == 0:
            new_time = time_to_round + timedelta(minutes=15 - reminder)
            return new_time
        return time_to_round

    def _crontab_range(self, start: datetime, stop: datetime, cron: CronTab):
        if cron.test(start):  # include start time in scheduling
            new_time = self._round_time_by_15(start)
            if new_time.hour == start.hour:
                yield start

        while True:
            start = cron.next(now=start, return_datetime=True, default_utc=True)
            new_time = self._round_time_by_15(start)
            if new_time.hour != start.hour:
                continue
            start = new_time

            if start > stop:
                break
            if start == stop:  # include stop time in scheduling
                yield start
                break

            start_time = start.time()
            if self._schedule_lowest_bound > start_time or self._schedule_highest_bound < start_time:
                continue

            yield start

    def schedule(self, schedule_in: Schedule):
        today = date.today()
        stop = datetime(
            year=today.year,
            month=today.month,
            day=today.day,
            hour=self._schedule_highest_bound.hour,
            minute=self._schedule_highest_bound.minute,
            second=self._schedule_highest_bound.second,
            microsecond=self._schedule_highest_bound.microsecond,
            tzinfo=timezone.utc,
        )
        stop = schedule_in.intake_finish if schedule_in.intake_finish and schedule_in.intake_finish < stop else stop

        for scheduled_datetime in self._crontab_range(
            schedule_in.intake_start, stop, CronTab(schedule_in.intake_period)
        ):
            yield schedule_in, scheduled_datetime

    async def get(self, user_id: int, schedule_id: int):
        try:
            result = await self._session.exec(
                select(Schedule).where((Schedule.user_id == user_id) & (Schedule.id == schedule_id))
            )
            return result.one_or_none()
        except MultipleResultsFound:
            await log.awarning("Multiple results returned from get schedule", schedule_id=schedule_id, user_id=user_id)
            return result.first()

    async def schedules(self, user_id):
        return await self._session.exec(select(Schedule.id).where(Schedule.user_id == user_id))

    async def next_takings(self, user_id: int, start: datetime, stop: datetime):
        schedules = await self._session.exec(select(Schedule).where(Schedule.user_id == user_id))
        contextvars = get_contextvars()
        parent_span_id = contextvars["span_id"]
        with bound_contextvars(span_id=str(uuid4())):
            await log.ainfo("Sent request to db", parent_span_id=parent_span_id)
        for schedule in schedules:
            schedule: Schedule
            for scheduled_datetime in self._crontab_range(start, stop, CronTab(schedule.intake_period)):
                yield schedule, scheduled_datetime

    async def create(self, schedule):
        schedule = Schedule(**schedule.model_dump())
        self._session.add(schedule)
        await self._session.commit()
        return schedule.id
