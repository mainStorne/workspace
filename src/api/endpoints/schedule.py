import structlog
from fastapi import HTTPException

from src.repositories.schedule_repository import ScheduleExpiredException, ScheduleNotFoundException

from ..deps.schedule_dependency import ScheduleRepositoryDependency
from ..routers.trace_router import TraceRouter
from ..schemas.schedule_schema import ScheduleCard, ScheduleCreate, ScheduleRead, TakingsRead

log = structlog.get_logger()
r = TraceRouter(tags=["Schedule"])


@r.post("/schedule", response_model=ScheduleRead)
async def create(schedule_repository: ScheduleRepositoryDependency, schedule: ScheduleCreate):
    schedule_id = await schedule_repository.create(schedule=schedule)
    return {"id": schedule_id}


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
    response = []
    for schedule in await schedule_repository.schedules(user_id):
        response.append({"id": schedule})
    return response


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
