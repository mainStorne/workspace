from typing import Callable

from sqlmodel.ext.asyncio.session import AsyncSession

from aibolit_app.grpc.server import Server
from aibolit_app.grpc.servicers.schedule_servicer import ScheduleServiceServicer
from aibolit_app.settings import EnvSettings


def make_grpc_server(port: int, db_session_maker: Callable[[], AsyncSession], settings: EnvSettings) -> Server:
    servicer = ScheduleServiceServicer(db_session_maker, settings)
    return Server(port, servicer)
