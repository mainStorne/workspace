from fastapi import APIRouter

from ...db import Schedule
from ...deps import Session
from .schema import ScheduleCreate, ScheduleRead

r = APIRouter()


@r.post("/schedule", response_model=ScheduleRead)
async def create(session: Session, schedule: ScheduleCreate):
    schedule_db = Schedule(**schedule.model_dump())
    session.add(schedule_db)
    await session.commit()
    return ScheduleRead(schedule_id=schedule_db.id)
