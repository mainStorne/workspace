import grpc
from structlog import get_logger

from aibolit_app.grpc.generated.schedule_pb2_grpc import ScheduleServiceServicer, add_ScheduleServiceServicer_to_server
from aibolit_app.grpc.interceptors.logging_interceptor import LoggingInterceptor

log = get_logger()


class Server:
    def __init__(self, port: int, servicer: ScheduleServiceServicer):
        self._server = grpc.aio.server(interceptors=[LoggingInterceptor()])
        add_ScheduleServiceServicer_to_server(servicer, self._server)
        self._server.add_insecure_port(f'[::]:{port}')

    async def wait_for_termination(self):
        await self._server.wait_for_termination()

    async def start(self):
        await log.ainfo('gRPC server is starting')
        await self._server.start()

    async def stop(self):
        await log.ainfo('gRPC server is stopping')
        await self._server.stop(None)
