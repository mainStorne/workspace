from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Callable

from google.protobuf.timestamp_pb2 import Timestamp
import grpc
from grpc.aio import ServicerContext
from pydantic import ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from aibolit_app.api.schemas.schedules import ScheduleCreate
from aibolit_app.grpc.generated.schedule_pb2 import (
    CreateScheduleRequest,
    CreateScheduleResponse,
    GetNextTakingsRequest,
    GetNextTakingsResponse,
    GetScheduleIdsRequest,
    GetScheduleIdsResponse,
    MakeScheduleRequest,
    MakeScheduleResponse,
)
from aibolit_app.grpc.generated.schedule_pb2_grpc import ScheduleServiceServicer as _ScheduleServiceServicer
from aibolit_app.integrations.schedules_repo import ScheduleRepo
from aibolit_app.services.schedules_service import ScheduleExpiredException, ScheduleNotFoundException, ScheduleService
from aibolit_app.settings import EnvSettings


class ScheduleServiceServicer(_ScheduleServiceServicer):
    def __init__(self, session_maker: Callable[[], AsyncSession], settings: EnvSettings):
        self._session_maker = session_maker
        self._settings = settings
        super().__init__()

    @asynccontextmanager
    async def schedule_service_dependency(self):
        async with self._session_maker() as session:
            yield ScheduleService(
                ScheduleRepo(session, self._settings.schedule_lowest_bound, self._settings.schedule_highest_bound),
                self._settings.next_takings_period,
            )

    async def CreateSchedule(self, request: CreateScheduleRequest, context: ServicerContext):
        async with self.schedule_service_dependency() as schedule_service:
            try:
                schedule = ScheduleCreate(
                    medicine_name=request.medicine_name,
                    intake_period=request.intake_period,
                    user_id=request.user_id,
                    intake_start=datetime.fromtimestamp(request.intake_start.seconds, tz=timezone.utc),
                    intake_finish=datetime.fromtimestamp(request.intake_finish.seconds, tz=timezone.utc)
                    if request.intake_finish.seconds != 0
                    else None,
                )
                schedule.validate_bound_datetime(
                    self._settings.schedule_lowest_bound, self._settings.schedule_highest_bound
                )
            except ValidationError:
                return await context.abort(grpc.StatusCode.ABORTED, 'Validation error')
            except ValueError as e:
                await context.abort(grpc.StatusCode.ABORTED, str(e))

            schedule_id = await schedule_service.create(schedule)
            return CreateScheduleResponse(id=schedule_id)

    async def MakeSchedule(self, request: MakeScheduleRequest, context: ServicerContext):
        async with self.schedule_service_dependency() as schedule_service:
            response = MakeScheduleResponse()
            try:
                schedule_gen = await schedule_service.schedule(request.user_id, request.schedule_id)
            except ScheduleNotFoundException:
                return await context.abort(grpc.StatusCode.NOT_FOUND)
            except ScheduleExpiredException:
                return await context.abort(grpc.StatusCode.ABORTED, 'Schedule is expired')

            for schedule, scheduled_datetime in schedule_gen:
                response.items.add(medicine_datetime=scheduled_datetime, medicine_name=schedule.medicine_name)
            return response

    async def GetScheduleIds(self, request: GetScheduleIdsRequest, context):
        async with self.schedule_service_dependency() as schedule_service:
            response = GetScheduleIdsResponse()
            for schedule_id in await schedule_service.schedules(request.user_id):
                response.ids.append(schedule_id)

            return response

    async def GetNextTakings(self, request: GetNextTakingsRequest, context):
        async with self.schedule_service_dependency() as schedule_service:
            response = GetNextTakingsResponse()
            async for schedule, scheduled_datetime in await schedule_service.next_takings(user_id=request.user_id):
                timestamp = Timestamp()
                timestamp.FromDatetime(scheduled_datetime)
                response.items.add(
                    medicine_name=schedule.medicine_name,
                    medicine_datetime=timestamp,
                    id=schedule.id,
                )
            return response
