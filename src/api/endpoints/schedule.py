import structlog
from fastapi import HTTPException, status

from src.repositories.schedule_repository import ScheduleExpiredException, ScheduleNotFoundException

from ..deps.schedule_dependency import ScheduleRepositoryDependency
from ..routers.trace_router import TraceRouter
from ..schemas.schema import ScheduleCard, ScheduleRead, TakingsRead

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
        schedule_gen = await schedule_repository.schedule(user_id, schedule_id)
    except ScheduleNotFoundException:
        raise HTTPException(status_code=404, detail="Not found") from None
    except ScheduleExpiredException:
        raise HTTPException(status_code=400, detail="Расписание истекло!") from None

    response = []
    for schedule, scheduled_datetime in schedule_gen:
        response.append(
            ScheduleCard.model_construct(medicine_name=schedule.medicine_name, medicine_datetime=scheduled_datetime)
        )
    return response


@r.get("/schedules", response_model=list[ScheduleRead])
async def schedules(user_id: int, schedule_repository: ScheduleRepositoryDependency):
    """Возвращает данные о выбранном расписании с рассчитанным  # noqa: RUF003
    графиком приёмов на день
    """  # noqa: RUF002
    # TODO: add new table users and link users to schedules. Change id to UUID type. Handle user not found error
    return await schedule_repository.schedules(user_id)


@r.get("/next_takings", response_model=list[TakingsRead])
async def next_takings(schedule_repository: ScheduleRepositoryDependency, user_id: int):
    """Возвращает данные о таблетках, которые необходимо принять  # noqa: RUF003
    в ближайшие период (например, в ближайший час). Период
    времени задается через параметры конфигурации сервиса
    """  # noqa: RUF002
    # TODO: handle user not found error
    response = []
    async for schedule, scheduled_datetime in await schedule_repository.next_takings(user_id=user_id):
        response.append(
            TakingsRead.model_construct(
                medicine_name=schedule.medicine_name,
                medicine_datetime=scheduled_datetime,
                id=schedule.id,
            )
        )
    return response
