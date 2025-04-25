from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetScheduleIdsRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    def __init__(self, user_id: _Optional[int] = ...) -> None: ...

class GetScheduleIdsResponse(_message.Message):
    __slots__ = ("ids",)
    IDS_FIELD_NUMBER: _ClassVar[int]
    ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, ids: _Optional[_Iterable[int]] = ...) -> None: ...

class MakeScheduleRequest(_message.Message):
    __slots__ = ("user_id", "schedule_id")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SCHEDULE_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    schedule_id: int
    def __init__(self, user_id: _Optional[int] = ..., schedule_id: _Optional[int] = ...) -> None: ...

class MakeScheduleResponseItem(_message.Message):
    __slots__ = ("medicine_name", "medicine_datetime")
    MEDICINE_NAME_FIELD_NUMBER: _ClassVar[int]
    MEDICINE_DATETIME_FIELD_NUMBER: _ClassVar[int]
    medicine_name: str
    medicine_datetime: _timestamp_pb2.Timestamp
    def __init__(self, medicine_name: _Optional[str] = ..., medicine_datetime: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class MakeScheduleResponse(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[MakeScheduleResponseItem]
    def __init__(self, items: _Optional[_Iterable[_Union[MakeScheduleResponseItem, _Mapping]]] = ...) -> None: ...

class CreateScheduleRequest(_message.Message):
    __slots__ = ("medicine_name", "intake_period", "user_id", "intake_finish")
    MEDICINE_NAME_FIELD_NUMBER: _ClassVar[int]
    INTAKE_PERIOD_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    INTAKE_FINISH_FIELD_NUMBER: _ClassVar[int]
    medicine_name: str
    intake_period: str
    user_id: int
    intake_finish: _timestamp_pb2.Timestamp
    def __init__(self, medicine_name: _Optional[str] = ..., intake_period: _Optional[str] = ..., user_id: _Optional[int] = ..., intake_finish: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateScheduleResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class GetNextTakingsRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    def __init__(self, user_id: _Optional[int] = ...) -> None: ...

class GetNextTakingsResponseItem(_message.Message):
    __slots__ = ("medicine_name", "intake_period", "id")
    MEDICINE_NAME_FIELD_NUMBER: _ClassVar[int]
    INTAKE_PERIOD_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    medicine_name: str
    intake_period: str
    id: int
    def __init__(self, medicine_name: _Optional[str] = ..., intake_period: _Optional[str] = ..., id: _Optional[int] = ...) -> None: ...

class GetNextTakingsResponse(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[GetNextTakingsResponseItem]
    def __init__(self, items: _Optional[_Iterable[_Union[GetNextTakingsResponseItem, _Mapping]]] = ...) -> None: ...
