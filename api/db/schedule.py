from ..modules.schedule.schema import ScheduleCreate
from .mixins import IDMixin


class Schedule(IDMixin, ScheduleCreate, table=True):
    __tablename__ = "schedules"
