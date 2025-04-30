from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header


class TraceRouter(APIRouter):
    def __init__(
        self,
        *,
        prefix="",
        tags=None,
        dependencies=None,
        default_response_class=...,
        responses=None,
        callbacks=None,
        routes=None,
        redirect_slashes=True,
        default=None,
        dependency_overrides_provider=None,
        route_class=...,
        on_startup=None,
        on_shutdown=None,
        lifespan=None,
        deprecated=None,
        include_in_schema=True,
        generate_unique_id_function=...,
    ):
        dependencies = dependencies or []
        dependencies.append(Depends(self._add_trace_documentation))
        super().__init__(prefix=prefix, tags=tags, dependencies=dependencies)

    @staticmethod
    def _add_trace_documentation(trace_id: Annotated[UUID | None, Header(alias="X-Trace-Id")] = None):
        return trace_id
