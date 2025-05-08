import grpc
from structlog import get_logger

from aibolit_app.grpc.generated.schedule_pb2_grpc import add_ScheduleServiceServicer_to_server
from aibolit_app.grpc.interceptors.logging_interceptor import LoggingInterceptor
from aibolit_app.grpc.servicers.schedule_servicer import ScheduleServiceServicer
from aibolit_app.settings import EnvSettings

log = get_logger()


class Server:
    def __init__(self, port: int, session_maker, db_engine, settings: EnvSettings):
        self._session_maker = session_maker
        self._db_engine = db_engine
        self._settings = settings
        self._server = grpc.aio.server(interceptors=[LoggingInterceptor()])
        add_ScheduleServiceServicer_to_server(
            ScheduleServiceServicer(self._session_maker, self._settings), self._server
        )
        self._server.add_insecure_port(f'[::]:{port}')

    async def wait_for_termination(self):
        await self._server.wait_for_termination()

    async def start(self):
        await log.ainfo('gRPC server is starting')
        await self._server.start()

    async def stop(self):
        await log.ainfo('gRPC server is stopping')
        await self._server.stop(None)
