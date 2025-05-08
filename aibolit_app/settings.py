from datetime import time, timedelta
from enum import StrEnum
from functools import lru_cache

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    DEV = 'DEV'
    PROD = 'PROD'


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='postgres_')
    username: str = Field(validation_alias='postgres_user')
    password: str
    host: str
    port: int
    db: str

    @property
    def sqlalchemy_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme='postgresql+asyncpg',
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.db,
            )
        )


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(extra='allow')
    next_takings_period: timedelta = Field(validation_alias='NEXT_TAKINGS_PERIOD')
    schedule_lowest_bound: time = time(hour=8)
    schedule_highest_bound: time = time(hour=22)
    environment: AppEnvironment = Field(validation_alias='APP_ENVIRONMENT')
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @model_validator(mode='after')
    def validate_bounds(self):
        if self.schedule_lowest_bound > self.schedule_highest_bound:
            raise ValueError('lowest bound must be lowest!')  # noqa: TRY003

        return self


@lru_cache
def get_env_settings() -> EnvSettings:
    return EnvSettings()
