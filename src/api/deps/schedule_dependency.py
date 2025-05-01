from typing import Annotated

from fastapi import Depends

from src.conf import settings
from src.repositories.schedule_repository import ScheduleRepository
from src.services.schedule_service import ScheduleService

from .session_dependency import GetSession


async def get_schedule_service(session: GetSession):
    return ScheduleService(session)


async def get_schedule_repository(schedule_service=Depends(get_schedule_service)):  # noqa: B008
    return ScheduleRepository(schedule_service, settings.NEXT_TAKINGS_PERIOD)


ScheduleRepositoryDependency = Annotated[ScheduleRepository, Depends(get_schedule_repository)]
