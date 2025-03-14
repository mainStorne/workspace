from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from .settings import Settings

settings = Settings()
engine = create_async_engine(settings.database.sqlalchemy_url)
session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
