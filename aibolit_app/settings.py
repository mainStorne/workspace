from datetime import time, timedelta
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource


class AppEnvironments(StrEnum):
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


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(yaml_file=Path(__file__).parent / 'settings.yml')
    app_environment: AppEnvironments
    app_version: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(extra='allow')
    next_takings_period: timedelta = Field(validation_alias='NEXT_TAKINGS_PERIOD')
    schedule_lowest_bound: time = time(hour=8)
    schedule_highest_bound: time = time(hour=22)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @model_validator(mode='after')
    def validate_bounds(self):
        if self.schedule_lowest_bound > self.schedule_highest_bound:
            raise ValueError('lowest bound must be lowest!')  # noqa: TRY003

        return self


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


@lru_cache
def get_env_settings() -> EnvSettings:
    return EnvSettings()
