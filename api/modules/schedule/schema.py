from datetime import datetime, timedelta
from typing import ClassVar

from crontab import CronTab
from pydantic import field_validator
from sqlalchemy import String
from sqlmodel import Field, SQLModel


class ScheduleCreate(SQLModel):
    crontab: ClassVar[CronTab]
    medicine_name: str
    intake_period: str = Field(
        description="Период приёмов записывается в cron синтаксисе, пример 0 12 * * * - каждый день в ровно 12 часов дня",
        schema_extra={"examples": ["0 12 * * *"]},
    )
    treatment_duration: timedelta | None = Field(description="Продолжительность лечения null - принимать постоянно")
    user_id: str = Field(sa_column=String(16), description="Медицинский полис состоящий из 16 цифр", max_length=16)

    @field_validator("intake_period", mode="after")
    @classmethod
    def validate_cron_expression(cls, value: str):
        """
        raise: ValueError
        """
        cls.crontab = CronTab(value)
        return value


class ScheduleRead(SQLModel):
    id: int


class ScheduleCard(SQLModel):
    medicine_name: str
    medicine_datetime: datetime
