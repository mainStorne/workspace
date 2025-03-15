from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from ...db import Schedule
from ...deps import Session
from ...utils import to_openapi
from .manager import schedule_manager
from .schema import ScheduleCard, ScheduleCreate, ScheduleRead

r = APIRouter()


@r.post("/schedule", response_model=ScheduleRead)
async def create(session: Session, schedule: ScheduleCreate):
    schedule_db = Schedule(**schedule.model_dump())
    session.add(schedule_db)
    await session.commit()
    return ScheduleRead(id=schedule_db.id)


ScheduleExpired = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Расписание истекло!")


@r.get(
    "/schedule",
    responses={404: {"detail": "Not found"}, **to_openapi(ScheduleExpired)},
    response_model=list[ScheduleCard],
)
async def schedule(session: Session, user_id: str, schedule_id: int):
    """Возвращает данные о выбранном расписании с рассчитанным
    графиком приёмов на день
    """  # noqa: RUF002
    schedule = await schedule_manager.get_or_404(session, user_id=user_id, id=schedule_id)
    # test for expired
    if schedule.treatment_duration and schedule.schedule_datetime + schedule.treatment_duration < datetime.now(
        tz=timezone.utc
    ):
        raise ScheduleExpired

    return schedule_manager.schedule(schedule)


@r.get("/schedules", response_model=list[ScheduleRead])
async def schedules(user_id: str, session: Session):
    return await schedule_manager.list(session, user_id=user_id)


@r.get("/next_takings")
async def next_takings(session: Session, user_id: str, schedule_id: int):
    pass
