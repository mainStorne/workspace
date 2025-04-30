from datetime import datetime, timezone

from structlog import get_logger

from src.conf import settings
from src.services.schedule_service import IScheduleService

log = get_logger()


class ScheduleRepositoryException(Exception): ...


class ScheduleNotFoundException(ScheduleRepositoryException):
    pass


class ScheduleExpiredException(ScheduleRepositoryException): ...


class ScheduleRepository:
    def __init__(self, schedule_service: IScheduleService):
        self._schedule_service = schedule_service

    async def schedule(self, user_id: int, schedule_id: int):
        schedule = await self._schedule_service.get(user_id, schedule_id=schedule_id)
        if not schedule:
            raise ScheduleNotFoundException

        if schedule.intake_finish and schedule.intake_finish < datetime.now(tz=timezone.utc):
            raise ScheduleExpiredException

        return self._schedule_service.schedule(schedule)

    async def next_takings(self, user_id: int):
        start = datetime.now(tz=timezone.utc)
        stop = start + settings.NEXT_TAKINGS_PERIOD
        return self._schedule_service.next_takings(user_id, start, stop)

    async def schedules(self, user_id: int):
        return await self._schedule_service.schedules(user_id)
