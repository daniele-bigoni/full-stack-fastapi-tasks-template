import warnings
from datetime import timedelta
import pytz
from typing import Literal, Union, Dict

from pydantic import (
    HttpUrl,
    AmqpDsn,
    PostgresDsn,
    computed_field,
    model_validator, SecretStr,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    TZ: str

    @property
    def TZINFO(self) -> pytz.BaseTzInfo:
        return pytz.timezone(self.TZ)

    # Postgres
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field
    @property
    def CELERY_BACKEND_DB_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="db+postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Mailing
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    # TODO: update type to EmailStr when sqlmodel supports it
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        flg = bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)
        if not flg:
            raise ValueError("Emails must be enabled.")
        return flg

    # TODO: update type to EmailStr when sqlmodel supports it
    EMAIL_TEST_USER: str = "test@example.com"

    # RabbitMQ
    RABBITMQ_PROTOCOL: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASSWORD: SecretStr

    @computed_field  # type: ignore[misc]
    @property
    def RABBITMQ_URI(self) -> AmqpDsn:
        return AmqpDsn.build(
            scheme=self.RABBITMQ_PROTOCOL,
            username=self.RABBITMQ_DEFAULT_USER,
            password=self.RABBITMQ_DEFAULT_PASSWORD.get_secret_value(),
            host=self.RABBITMQ_HOST,
            port=self.RABBITMQ_PORT
        )

    def _check_default_secret(self, var_name: str, value: SecretStr | str | None) -> None:
        if (value is not None) and ("changethis" in str(value)):
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    def _secrets_list(self) -> list:
        return [
            "POSTGRES_PASSWORD",
            "RABBITMQ_DEFAULT_PASSWORD",
            "SMTP_PASSWORD",
        ]

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        for key in self._secrets_list():
            self._check_default_secret(key, getattr(self, key))
        return self


class CeleryConfig(BaseSettings):
    """
    All these variables can be overridden by environment variables
    """

    database_table_schemas: dict = {
        'task': 'public',
        'group': 'public',
    }  # Keep this to public otherwise one needs to create dedicated schemas through the datamodel
    database_table_names: dict = {
        'task': 'celery_taskmeta',
        'group': 'celery_groupmeta',
    }
    enable_utc: bool = True
    result_expires: Union[None, float, timedelta] = None
    result_persistent: bool = True
    result_extended: bool = True
    task_create_missing_queues: bool = True
    task_default_queue: str = 'celery'
    broker_use_ssl: Union[None, dict] = None  # Not set for now
    broker_pool_limit: Union[None, int] = 10
    broker_connection_retry: bool = True
    broker_connection_timeout: float = 4.0
    broker_connection_retry_on_startup: bool = True
    broker_connection_max_retries: Union[None, int] = 100

    beat_schedule: dict = {}  # Don't know yet if this goes here or only in the worker

    task_routes: Dict[str, dict] = {
        'add': {'queue': 'shared'},
        'multiply': {'queue': 'alpha'},
        'sample-normal': {'queue': 'beta'},
        'multiply-by-summation': {'queue': 'alpha'}
    }

