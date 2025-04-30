from datetime import datetime, timezone

from structlog import get_logger

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

    # async def _next_takings(self, session: AsyncSession, user_id: str):
    #     start = datetime.now(tz=timezone.utc)
    #     stop = start + settings.NEXT_TAKINGS_PERIOD
    #     schedules = await self.list(session, user_id=user_id)
    #     contextvars = get_contextvars()
    #     parent_span_id = contextvars["span_id"]
    #     with bound_contextvars(span_id=str(uuid4())):
    #         await log.ainfo("Sent request to db", parent_span_id=parent_span_id)
    #     for schedule in schedules:
    #         schedule: Schedule
    #         expired_datetime = schedule.intake_finish if schedule.intake_finish else stop
    #         for scheduled_datetime in crontab_range(start, stop, CronTab(schedule.intake_period)):
    #             if scheduled_datetime > expired_datetime:
    #                 break
    #             yield schedule, scheduled_datetime

    # async def next_takings(self, session: AsyncSession, user_id: str):
    #     scheduled = []
    #     async for schedule, scheduled_datetime in self._next_takings(session, user_id):
    #         scheduled.append(
    #             TakingsRead.model_construct(
    #                 medicine_name=schedule.medicine_name,
    #                 medicine_datetime=scheduled_datetime,
    #                 id=schedule.id,
    #             )
    #         )
    #     return scheduled
