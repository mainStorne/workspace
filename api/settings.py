from datetime import timedelta

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="postgres_")
    username: str = Field(validation_alias="postgres_user")
    password: str
    host: str
    port: int
    db: str

    @property
    def sqlalchemy_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.db,
            )
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")
    NEXT_TAKINGS_PERIOD: timedelta
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
