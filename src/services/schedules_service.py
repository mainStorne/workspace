from datetime import datetime, timedelta, timezone

from structlog import get_logger

from src.api.schemas.schedules import ScheduleCreate
from src.integrations.schedules_repo import IScheduleRepo

log = get_logger()


class ScheduleServiceException(Exception): ...


class ScheduleNotFoundException(ScheduleServiceException): ...


class ScheduleExpiredException(ScheduleServiceException): ...


class ScheduleService:
    def __init__(self, schedule_repo: IScheduleRepo, next_takings_period: timedelta):
        self._schedule_repo = schedule_repo
        self._next_takings_period = next_takings_period

    async def schedule(self, user_id: int, schedule_id: int):
        schedule = await self._schedule_repo.get(user_id, schedule_id=schedule_id)
        if not schedule:
            raise ScheduleNotFoundException

        if schedule.intake_finish and schedule.intake_finish <= datetime.now(tz=timezone.utc):
            raise ScheduleExpiredException

        return self._schedule_repo.schedule(schedule)

    async def next_takings(self, user_id: int):
        start = datetime.now(tz=timezone.utc)
        stop = start + self._next_takings_period
        return self._schedule_repo.next_takings(user_id, start, stop)

    async def schedules(self, user_id: int):
        return await self._schedule_repo.schedules(user_id)

    async def create(self, schedule: ScheduleCreate):
        return await self._schedule_repo.create(schedule)
