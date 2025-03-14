from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from .conf import session_maker


async def get_session():
    async with session_maker() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_session)]
