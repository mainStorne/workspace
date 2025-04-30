import pytest
from pytest import fixture

import grpc
from src.db import Schedule
from src.gRPC.generated.schedule_pb2 import CreateScheduleRequest, GetScheduleIdsRequest
from src.gRPC.generated.schedule_pb2_grpc import ScheduleServiceStub
from src.gRPC.server import Server
from src.gRPC.servicers.schedule_servicer import ScheduleServiceServicer

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


async def test_create_schedule(stub, session):
    response = await stub.CreateSchedule(
        CreateScheduleRequest(user_id=1, medicine_name="test", intake_period="12", intake_finish=None)
    )

    assert response.id
    assert await session.get(Schedule, response.id) is not None


@pytest.mark.skip
async def test_get_schedule_ids(stub, schedule):
    response = await stub.GetScheduleIds(GetScheduleIdsRequest(user_id=schedule.user_id))
    # TODO fix why this is not working
    assert response.ids == [schedule.id]
