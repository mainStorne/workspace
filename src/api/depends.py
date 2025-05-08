from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from src.integrations.schedules_repo import ScheduleRepo
from src.services.schedules_service import ScheduleService
from src.settings import EnvSettings, get_env_settings


async def get_db_depends(request: Request):
    db_sessionmaker: async_sessionmaker = request.state.db_sessionmaker
    async with db_sessionmaker() as session:
        yield session


SessionDependency = Annotated[AsyncSession, Depends(get_db_depends)]


EnvSettingsDependency = Annotated[EnvSettings, Depends(get_env_settings)]


async def get_schedule_repo(session: SessionDependency, settings: EnvSettingsDependency):
    return ScheduleRepo(session, settings.schedule_lowest_bound, settings.schedule_highest_bound)


async def get_schedule_service(*, schedule_repo=Depends(get_schedule_repo), settings: EnvSettingsDependency):  # noqa: B008
    return ScheduleService(schedule_repo, settings.next_takings_period)


ScheduleServiceDependency = Annotated[ScheduleService, Depends(get_schedule_service)]
