from datetime import datetime, time, timezone

from crontab import CronTab
from pydantic import field_validator, model_validator

from aibolit_app.api.schemas.schedules.generated import ScheduleCreate as _ScheduleCreate


class ScheduleCreate(_ScheduleCreate):
    intake_start: datetime = datetime.now(tz=timezone.utc)

    @model_validator(mode='after')
    def validate_intake_finish(self):
        if self.intake_finish is not None and self.intake_finish <= self.intake_start:
            raise ValueError("intake_finish can't be less then intake_start!")  # noqa: TRY003
        return self

    @field_validator('intake_start', mode='after')
    @classmethod
    def validate_intake_start(cls, value: datetime):
        if value < datetime.now(timezone.utc):
            raise ValueError("intake_start can't be less then now datetime")  # noqa: TRY003
        return value

    def validate_bound_datetime(self, lowest: time, highest: time) -> None:
        """
        raises: ValueError
        """
        intake_finish_time = self.intake_finish.time()
        if intake_finish_time < lowest:
            raise ValueError(f'intake_finish_time is less then lowest time {lowest.strftime("%H:%m")}')  # noqa: EM102, TRY003
        if intake_finish_time > highest:
            raise ValueError(f'intake_finish_time is more then highest time {highest.strftime("%H:%m")}')  # noqa: EM102, TRY003

        intake_start_time = self.intake_start.time()
        if intake_start_time < lowest:
            raise ValueError(f'intake_start_time is less then lowest time {lowest.strftime("%H:%m")}')  # noqa: EM102, TRY003
        if intake_start_time > highest:
            raise ValueError(f'intake_start_time is more then highest time {highest.strftime("%H:%m")}')  # noqa: EM102, TRY003

    @field_validator('intake_period', mode='after')
    @classmethod
    def validate_cron_expression(cls, value: str):
        try:
            crontab = CronTab(value)
        except ValueError:
            raise ValueError('cron expression is wrong!')  # noqa: B904, TRY003
        # big cron syntax * * * * * * (with seconds and years)
        if crontab.matchers.second.input == '*' or crontab.matchers.minute.input == '*':
            raise ValueError("Schedule can't run every second or every minute")  # noqa: TRY003

        return value
