from datetime import datetime

from sqlalchemy import Column, DateTime, text
from sqlmodel import Field

from ..modules.schedule.schema import ScheduleCreate
from .mixins import IDMixin


class Schedule(IDMixin, ScheduleCreate, table=True):
    __tablename__ = "schedules"
    schedule_datetime: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
