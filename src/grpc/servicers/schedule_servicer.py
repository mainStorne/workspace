from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp
from pydantic import ValidationError

import grpc
from grpc.aio import ServicerContext
from src.repositories.schedule_repository import ScheduleExpiredException, ScheduleNotFoundException, ScheduleRepository

from ...api.schemas.schema import ScheduleCreate
from ..generated.schedule_pb2 import (
    CreateScheduleRequest,
    CreateScheduleResponse,
    GetNextTakingsRequest,
    GetNextTakingsResponse,
    GetScheduleIdsRequest,
    GetScheduleIdsResponse,
    MakeScheduleRequest,
    MakeScheduleResponse,
)
from ..generated.schedule_pb2_grpc import ScheduleServiceServicer as _ScheduleServiceServicer
from ..injections.schedule_inject import schedule_inject


class ScheduleServiceServicer(_ScheduleServiceServicer):
    @schedule_inject
    async def CreateSchedule(
        self, request: CreateScheduleRequest, context: ServicerContext, schedule_repository: ScheduleRepository
    ):
        try:
            schedule = ScheduleCreate(
                medicine_name=request.medicine_name,
                intake_period=request.intake_period,
                user_id=request.user_id,
                intake_finish=datetime.fromtimestamp(request.intake_finish.seconds, tz=timezone.utc)
                if request.intake_finish.seconds != 0
                else None,
            )
        except ValidationError:
            return await context.abort(grpc.StatusCode.ABORTED, "Validation error")

        schedule_id = await schedule_repository.create(schedule)
        return CreateScheduleResponse(id=schedule_id)

    @schedule_inject
    async def MakeSchedule(
        self, request: MakeScheduleRequest, context: ServicerContext, schedule_repository: ScheduleRepository
    ):
        response = MakeScheduleResponse()
        try:
            schedule_gen = await schedule_repository.schedule(request.user_id, request.schedule_id)
        except ScheduleNotFoundException:
            return await context.abort(grpc.StatusCode.NOT_FOUND)
        except ScheduleExpiredException:
            return await context.abort(grpc.StatusCode.ABORTED, "Schedule is expired")

        for schedule, scheduled_datetime in schedule_gen:
            response.items.add(medicine_datetime=scheduled_datetime, medicine_name=schedule.medicine_name)
        return response

    @schedule_inject
    async def GetScheduleIds(self, request: GetScheduleIdsRequest, context, schedule_repository: ScheduleRepository):
        response = GetScheduleIdsResponse()
        for schedule_id in await schedule_repository.schedules(request.user_id):
            response.ids.append(schedule_id)

        return response

    @schedule_inject
    async def GetNextTakings(self, request: GetNextTakingsRequest, context, schedule_repository: ScheduleRepository):
        response = GetNextTakingsResponse()
        async for schedule, scheduled_datetime in await schedule_repository.next_takings(user_id=request.user_id):
            timestamp = Timestamp()
            timestamp.FromDatetime(scheduled_datetime)
            response.items.add(
                medicine_name=schedule.medicine_name,
                medicine_datetime=timestamp,
                id=schedule.id,
            )
        return response
