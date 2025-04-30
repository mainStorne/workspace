import structlog
from fastapi import HTTPException, status

from src.repositories.schedule_repository import ScheduleExpiredException, ScheduleNotFoundException

from ..deps.schedule_dependency import ScheduleRepositoryDependency
from ..routers.trace_router import TraceRouter
from ..schemas.schema import ScheduleCard

log = structlog.get_logger()
r = TraceRouter(tags=["Schedule"])


# @r.post("/schedule", response_model=ScheduleRead)
# async def create(session: Session, schedule: ScheduleCreate):
#     schedule_db = Schedule(**schedule.model_dump())
#     session.add(schedule_db)
#     await session.commit()
#     return ScheduleRead(id=schedule_db.id)


ScheduleExpired = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="")


@r.get(
    "/schedule",
    responses={404: {"detail": "Not found"}, 400: {"detail": "Расписание истекло!"}},
    response_model=list[ScheduleCard],
)
async def schedule(*, schedule_repository: ScheduleRepositoryDependency, user_id: int, schedule_id: int):
    """Возвращает данные о выбранном расписании с рассчитанным
    графиком приёмов на день
    """  # noqa: RUF002
    try:
        return await schedule_repository.schedule(user_id, schedule_id)
    except ScheduleNotFoundException:
        raise HTTPException(status_code=404, detail="Not found") from None
    except ScheduleExpiredException:
        raise HTTPException(status_code=400, detail="Расписание истекло!") from None


# @r.get("/schedules", response_model=list[ScheduleRead])
# async def schedules(user_id: int, session: Session):
#     """Возвращает данные о выбранном расписании с рассчитанным  # noqa: RUF003
#     графиком приёмов на день
#     """
#     return await schedule_manager.list(session, user_id=user_id)


# @r.get("/next_takings", response_model=list[TakingsRead])
# async def next_takings(session: Session, user_id: int):
#     """Возвращает данные о таблетках, которые необходимо принять  # noqa: RUF003
#     в ближайшие период (например, в ближайший час). Период
#     времени задается через параметры конфигурации сервиса
#     """
#     return await schedule_manager.next_takings(session, user_id=user_id)
