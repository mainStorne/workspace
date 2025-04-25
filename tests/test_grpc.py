import grpc
import pytest
from pytest import fixture

from api.gRPC.generated.schedule_pb2 import CreateScheduleRequest
from api.gRPC.generated.schedule_pb2_grpc import ScheduleServiceStub
from api.gRPC.server import Server
from api.gRPC.servicers.schedule_server import ScheduleServiceServicer

pytestmark = pytest.mark.anyio


@fixture(autouse=True, scope="session")
async def server():
    s = Server(port=50051, servicer=ScheduleServiceServicer())
    await s.start()
    yield
    await s.stop()


@fixture()
async def stub():
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        yield ScheduleServiceStub(channel=channel)


async def test_make_schedule(stub):
    response = await stub.CreateSchedule(
        CreateScheduleRequest(user_id=1, medicine_name="test", intake_period="8 12 * * *", intake_finish=None)
    )

    assert response.id
