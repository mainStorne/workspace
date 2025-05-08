from fastapi import APIRouter, HTTPException

from aibolit_app.api.depends import EnvSettingsDependency, ScheduleServiceDependency
from aibolit_app.api.schemas.schedules import ScheduleCard, ScheduleCreate, ScheduleRead, TakingsRead
from aibolit_app.services.schedules_service import ScheduleExpiredException, ScheduleNotFoundException

r = APIRouter(tags=['Schedule'])


@r.get('/schedules')
async def schedules(user_id: int, schedule_repository: ScheduleServiceDependency) -> list[ScheduleRead]:
    """Возвращает данные о выбранном расписании с рассчитанным  # noqa: RUF003
    графиком приёмов на день
    """  # noqa: RUF002
    response = []
    for schedule in await schedule_repository.schedules(user_id):
        response.append({'id': schedule})  # noqa: PERF401
    return response


@r.post('/schedule')
async def create(
    schedule_repository: ScheduleServiceDependency, schedule: ScheduleCreate, settings: EnvSettingsDependency
) -> ScheduleRead:
    try:
        schedule.validate_bound_datetime(settings.schedule_lowest_bound, settings.schedule_highest_bound)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))  # noqa: B904
    schedule_id = await schedule_repository.create(schedule=schedule)
    return {'id': schedule_id}


@r.get(
    '/schedule',
    responses={404: {'detail': 'Not found'}, 400: {'detail': 'Расписание истекло!'}},
)
async def schedule(
    *, schedule_repository: ScheduleServiceDependency, user_id: int, schedule_id: int
) -> list[ScheduleCard]:
    """Возвращает данные о выбранном расписании с рассчитанным
    графиком приёмов на день
    """  # noqa: RUF002

    try:
        schedule_gen = await schedule_repository.schedule(user_id, schedule_id)
    except ScheduleNotFoundException:
        raise HTTPException(status_code=404, detail='Not found') from None
    except ScheduleExpiredException:
        raise HTTPException(status_code=400, detail='Расписание истекло!') from None

    response = []
    for schedule, scheduled_datetime in schedule_gen:
        response.append(
            ScheduleCard.model_construct(medicine_name=schedule.medicine_name, medicine_datetime=scheduled_datetime)
        )
    return response


@r.get('/next_takings')
async def next_takings(schedule_repository: ScheduleServiceDependency, user_id: int) -> list[TakingsRead]:
    """Возвращает данные о таблетках, которые необходимо принять  # noqa: RUF003
    в ближайшие период (например, в ближайший час). Период
    времени задается через параметры конфигурации сервиса
    """  # noqa: RUF002
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
