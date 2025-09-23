import secrets
from typing import Annotated, Any

from pydantic import AnyUrl, BeforeValidator, computed_field, SecretStr, model_validator
from typing_extensions import Self

from stack_settings import Settings as GeneralSettings
from stack_settings import CeleryConfig as GeneralCeleryConfig


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(GeneralSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 60 minutes * 24 hours * 8 days = 8 days
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    FRONTEND_HOST: str = "http://localhost:5173"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        lst_cors_origins = [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]
        return lst_cors_origins

    # Admin user
    # TODO: update type to EmailStr when sqlmodel supports it
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: SecretStr
    USERS_OPEN_REGISTRATION: bool = False

    OAUTH_FUSIONAUTH_ACCESS_TOKEN_URL: str
    OAUTH_FUSIONAUTH_AUTHORIZE_URL: str
    OAUTH_FUSIONAUTH_USERINFO_URL: str

    OAUTH_FUSIONAUTH_CLIENT_ID_APP_A: str
    OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_A: str

    OAUTH_FUSIONAUTH_CLIENT_ID_APP_B: str
    OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_B: str

    def _secrets_list(self) -> list:
        lst = super()._secrets_list()
        lst.extend([
            "SECRET_KEY",
            "FIRST_SUPERUSER_PASSWORD",
            "OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_A",
            "OAUTH_FUSIONAUTH_CLIENT_SECRET_APP_B"
        ])
        return lst


settings = Settings()


class CeleryConfig(GeneralCeleryConfig):
    pass


celery_config = CeleryConfig()
