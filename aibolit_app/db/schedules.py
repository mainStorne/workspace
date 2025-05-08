from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime
from sqlmodel import Field, SQLModel

from aibolit_app.db.mixins import IDMixin


class Schedule(IDMixin, SQLModel, table=True):
    __tablename__ = 'schedules'
    medicine_name: str = Field(index=True)
    intake_period: str = Field(
        description='Период приёмов записывается в [cron синтаксисе](https://en.wikipedia.org/wiki/Cron#CRON_expression), пример 0 12 * * * - каждый день в ровно 12 часов дня. **W и # символы не поддерживаются**',
        schema_extra={'examples': ['12']},
    )
    user_id: int = Field(sa_column=Column(BigInteger))
    intake_finish: datetime | None = Field(
        description='Конец лечения, null - если нет ограничения в длительности лечения',
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    intake_start: datetime = Field(
        default=datetime.now(tz=timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False)
    )
