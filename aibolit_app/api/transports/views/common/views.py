from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from pydantic import BaseModel

from aibolit_app.settings import AppSettings, get_app_settings

common_router = APIRouter(tags=['Common'])


class Root(BaseModel):
    version: str


@common_router.get('/')
def _get_root(
    settings: Annotated[AppSettings, Depends(get_app_settings)],
) -> Root:
    return {'version': settings.app_version}
