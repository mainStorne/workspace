from uuid import UUID

from sqlmodel import Field, text


class IDMixin:
    id: int | None = Field(default=None, primary_key=True)


class UUIDMixin:
    id: UUID = Field(sa_column_kwargs={"server_default": text("uuid_generate_v4()")}, primary_key=True)
