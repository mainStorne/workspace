# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""

import grpc

from aibolit_app.grpc.generated import schedule_pb2 as schedule__pb2

GRPC_GENERATED_VERSION = '1.71.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower

    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in schedule_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class ScheduleServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateSchedule = channel.unary_unary(
            '/schedule.ScheduleService/CreateSchedule',
            request_serializer=schedule__pb2.CreateScheduleRequest.SerializeToString,
            response_deserializer=schedule__pb2.CreateScheduleResponse.FromString,
            _registered_method=True,
        )
        self.GetScheduleIds = channel.unary_unary(
            '/schedule.ScheduleService/GetScheduleIds',
            request_serializer=schedule__pb2.GetScheduleIdsRequest.SerializeToString,
            response_deserializer=schedule__pb2.GetScheduleIdsResponse.FromString,
            _registered_method=True,
        )
        self.MakeSchedule = channel.unary_unary(
            '/schedule.ScheduleService/MakeSchedule',
            request_serializer=schedule__pb2.MakeScheduleRequest.SerializeToString,
            response_deserializer=schedule__pb2.MakeScheduleResponse.FromString,
            _registered_method=True,
        )
        self.GetNextTakings = channel.unary_unary(
            '/schedule.ScheduleService/GetNextTakings',
            request_serializer=schedule__pb2.GetNextTakingsRequest.SerializeToString,
            response_deserializer=schedule__pb2.GetNextTakingsResponse.FromString,
            _registered_method=True,
        )


class ScheduleServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CreateSchedule(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetScheduleIds(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MakeSchedule(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetNextTakings(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ScheduleServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'CreateSchedule': grpc.unary_unary_rpc_method_handler(
            servicer.CreateSchedule,
            request_deserializer=schedule__pb2.CreateScheduleRequest.FromString,
            response_serializer=schedule__pb2.CreateScheduleResponse.SerializeToString,
        ),
        'GetScheduleIds': grpc.unary_unary_rpc_method_handler(
            servicer.GetScheduleIds,
            request_deserializer=schedule__pb2.GetScheduleIdsRequest.FromString,
            response_serializer=schedule__pb2.GetScheduleIdsResponse.SerializeToString,
        ),
        'MakeSchedule': grpc.unary_unary_rpc_method_handler(
            servicer.MakeSchedule,
            request_deserializer=schedule__pb2.MakeScheduleRequest.FromString,
            response_serializer=schedule__pb2.MakeScheduleResponse.SerializeToString,
        ),
        'GetNextTakings': grpc.unary_unary_rpc_method_handler(
            servicer.GetNextTakings,
            request_deserializer=schedule__pb2.GetNextTakingsRequest.FromString,
            response_serializer=schedule__pb2.GetNextTakingsResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler('schedule.ScheduleService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('schedule.ScheduleService', rpc_method_handlers)


# This class is part of an EXPERIMENTAL API.


class ScheduleService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CreateSchedule(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/schedule.ScheduleService/CreateSchedule',
            schedule__pb2.CreateScheduleRequest.SerializeToString,
            schedule__pb2.CreateScheduleResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True,
        )

    @staticmethod
    def GetScheduleIds(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/schedule.ScheduleService/GetScheduleIds',
            schedule__pb2.GetScheduleIdsRequest.SerializeToString,
            schedule__pb2.GetScheduleIdsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True,
        )

    @staticmethod
    def MakeSchedule(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/schedule.ScheduleService/MakeSchedule',
            schedule__pb2.MakeScheduleRequest.SerializeToString,
            schedule__pb2.MakeScheduleResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True,
        )

    @staticmethod
    def GetNextTakings(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/schedule.ScheduleService/GetNextTakings',
            schedule__pb2.GetNextTakingsRequest.SerializeToString,
            schedule__pb2.GetNextTakingsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True,
        )
