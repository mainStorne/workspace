from datetime import datetime, timedelta
from re import compile

from crontab import CronTab
from pydantic import field_validator
from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel

cron_patter = compile(r"")


class ScheduleCreate(SQLModel):
    medicine_name: str
    intake_period: str = Field(
        description="Период приёмов записывается в [cron синтаксисе](https://en.wikipedia.org/wiki/Cron#CRON_expression), пример 0 12 * * * - каждый день в ровно 12 часов дня. **W и # символы не поддерживаются**",
        schema_extra={"examples": ["0 12 * * *"]},
    )
    treatment_duration: timedelta | None = Field(description="Продолжительность лечения null - принимать постоянно")
    user_id: int = Field(sa_column=Column(BigInteger))

    @field_validator("treatment_duration", mode="after")
    @classmethod
    def validate_treatment_duration(cls, value: timedelta | None):
        if value is not None and value.total_seconds() <= 3600:
            raise ValueError("treatment_duration can't be negative or so small!")  # noqa: TRY003
        return value

    @field_validator("intake_period", mode="after")
    @classmethod
    def validate_cron_expression(cls, value: str):
        crontab = CronTab(value)
        # big cron syntax * * * * * * (with seconds and years)
        if (
            crontab.matchers.second.input == "*"
            or crontab.matchers.minute.input == "*"
            or crontab.matchers.year.input != "*"
        ):
            raise ValueError("Schedule can't run every second or in specific year")  # noqa: TRY003
        if crontab.matchers.hour.input.isdigit():
            hour = int(crontab.matchers.hour.input)
            if (hour < 8 or hour > 22) or ((hour == 8 or hour == 22) and crontab.matchers.minute.input != "0"):
                raise ValueError("Schedule must be in interval from 8 to 22 hours")  # noqa: TRY003

        return value


class ScheduleRead(SQLModel):
    id: int


class ScheduleCard(SQLModel):
    medicine_name: str
    medicine_datetime: datetime


class TakingsRead(ScheduleCard):
    id: int
