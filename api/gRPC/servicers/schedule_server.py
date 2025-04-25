from datetime import datetime, timezone

import grpc
from grpc.aio import ServicerContext
from pydantic import ValidationError

from ...conf import session_maker
from ...db import Schedule

# from ..generated import  schedule_pb2_grpc
from ...modules.schedule.manager import schedule_manager
from ...modules.schedule.schema import ScheduleCreate
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


class ScheduleServiceServicer(_ScheduleServiceServicer):
    async def CreateSchedule(self, request: CreateScheduleRequest, context: ServicerContext):
        try:
            schedule = ScheduleCreate(
                medicine_name=request.medicine_name,
                intake_period=request.intake_period,
                user_id=request.user_id,
                intake_finish=datetime.fromtimestamp(request.intake_finish.seconds, tz=timezone.utc),
            )
        except ValidationError:
            return await context.abort(grpc.StatusCode.ABORTED, "Validation error")
        async with session_maker() as session:
            schedule = Schedule(**schedule.model_dump())
            session.add(schedule)
            await session.commit()
        return CreateScheduleResponse(id=schedule.id)

    async def MakeSchedule(self, request: MakeScheduleRequest, context: ServicerContext):
        response = MakeScheduleResponse()
        async with session_maker() as session:
            schedule: Schedule | None = await schedule_manager.get(
                session, user_id=request.user_id, id=request.schedule_id
            )

        if not schedule:
            return await context.abort(grpc.StatusCode.NOT_FOUND)

        # test for expired
        if schedule.intake_finish and schedule.intake_finish < datetime.now(tz=timezone.utc):
            return await context.abort(grpc.StatusCode.ABORTED, "Schedule is expired")

        for scheduled_datetime in schedule_manager._schedule(schedule):
            response.items.add(medicine_datetime=scheduled_datetime, medicine_name=schedule.medicine_name)

        return response

    async def GetScheduleIds(self, request: GetScheduleIdsRequest, context):
        response = GetScheduleIdsResponse()
        async with session_maker() as session:
            for schedule in await schedule_manager.list(session, user_id=request.user_id):
                response.ids.append(schedule.id)

        return response

    async def GetNextTakings(self, request: GetNextTakingsRequest, context):
        response = GetNextTakingsResponse()
        async with session_maker() as session:
            for schedule, scheduled_datetime in await schedule_manager._next_takings(session, user_id=request.user_id):
                response.items.add(
                    medicine_name=schedule.medicine_name,
                    medicine_datetime=scheduled_datetime,
                    id=schedule.id,
                )
        return response
