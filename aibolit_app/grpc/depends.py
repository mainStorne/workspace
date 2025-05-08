from functools import wraps

from aibolit_app.conf import session_maker, settings
from aibolit_app.integrations.schedules_repo import ScheduleRepo


def schedule_inject(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        async with session_maker() as session:
            schedule_repository = ScheduleRepo(ScheduleRepo(session), settings.next_takings_period)
            return await func(*args, **kwargs, schedule_repository=schedule_repository)

    return wrapped
