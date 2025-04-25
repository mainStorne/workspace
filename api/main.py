import asyncio
from logging import DEBUG, basicConfig

import grpc

from api.grpc.generated import schedule_pb2_grpc
from api.grpc.servicers.schedule_server import ScheduleServiceServicer

basicConfig(level=DEBUG)


async def main():
    server = grpc.aio.server()
    schedule_pb2_grpc.add_ScheduleServiceServicer_to_server(ScheduleServiceServicer(), server)
    server.add_insecure_port("[::]:8080")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(main())
