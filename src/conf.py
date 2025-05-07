from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.settings import EnvSettings

settings = EnvSettings()
engine = create_async_engine(settings.database.sqlalchemy_url, plugins=["geoalchemy2"])
session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
