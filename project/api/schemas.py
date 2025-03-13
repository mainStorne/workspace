from sqlalchemy import String
from sqlmodel import Field, SQLModel


class ScheduleCreate(SQLModel):
    medicine_name: str
    intake_period: str = Field(
        description="Период приёмов записывается в cron синтаксисе, пример 0 12 * * * - каждый день в ровно 12 часов дня"
    )
    treatment_duration: str
    user_id: str = Field(sa_column=String(16), description="Медицинский полис состоящий из 16 цифр")


class ScheduleRead(SQLModel):
    schedule_id: int
