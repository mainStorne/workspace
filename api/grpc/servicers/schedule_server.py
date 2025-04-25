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
    MakeScheduleRequest,
    MakeScheduleResponse,
    MakeScheduleResponseItem,
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
        items = []
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
            items.append(
                MakeScheduleResponseItem(
                    medicine_datetime=scheduled_datetime,
                    medicine_name=schedule.medicine_name,
                )
            )

        return MakeScheduleResponse(items)
