from functools import wraps

from src import settings
from src.conf import session_maker
from src.repositories.schedule_repository import ScheduleRepository
from src.services.schedule_service import ScheduleService


def schedule_inject(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        async with session_maker() as session:
            schedule_repository = ScheduleRepository(ScheduleService(session), settings.NEXT_TAKINGS_PERIOD)
            result = await func(*args, **kwargs, schedule_repository=schedule_repository)
        return result

    return wrapped
