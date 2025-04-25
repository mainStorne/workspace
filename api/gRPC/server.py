import grpc

from .generated.schedule_pb2_grpc import ScheduleServiceServicer, add_ScheduleServiceServicer_to_server


class Server:
    def __init__(self, servicer: ScheduleServiceServicer, port: int):
        self._server = grpc.aio.server()
        add_ScheduleServiceServicer_to_server(servicer, self._server)
        self._server.add_insecure_port(f"[::]:{port}")

    async def wait_for_termination(self):
        await self._server.wait_for_termination()

    async def start(self):
        await self._server.start()

    async def stop(self):
        await self._server.stop(None)
