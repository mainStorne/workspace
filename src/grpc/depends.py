from functools import wraps

from src.conf import session_maker, settings
from src.integrations.schedules_repo import ScheduleRepo


def schedule_inject(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        async with session_maker() as session:
            schedule_repository = ScheduleRepo(ScheduleRepo(session), settings.next_takings_period)
            result = await func(*args, **kwargs, schedule_repository=schedule_repository)
        return result

    return wrapped
