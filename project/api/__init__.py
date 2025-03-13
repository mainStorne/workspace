from fastapi import APIRouter

from .schemas import ScheduleCreate

r = APIRouter()


@r.post("/schedule")
async def create(schedule: ScheduleCreate):
    pass
