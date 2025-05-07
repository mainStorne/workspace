from datetime import datetime, timezone

from crontab import CronTab
from pydantic import field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema
from sqlmodel import Field

from src.api.schemas.schedules.generated import ScheduleCreate as _ScheduleCreate


class ScheduleCreate(_ScheduleCreate):
    intake_start: SkipJsonSchema[datetime] = Field(default=datetime.now(tz=timezone.utc))

    @model_validator(mode="after")
    def validate_intake_finish(self):
        if self.intake_finish is not None and self.intake_finish <= self.intake_start:
            raise ValueError("intake_finish can't be less then now or equal!")  # noqa: TRY003
        return self

    @field_validator("intake_period", mode="after")
    @classmethod
    def validate_cron_expression(cls, value: str):
        value = f"0 {value} * * *"
        try:
            crontab = CronTab(value)
        except ValueError:
            raise ValueError("cron expression is wrong!")  # noqa: B904, TRY003
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
