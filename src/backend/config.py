"""Config file for Pydantic and FastAPI, using environment variables."""

import logging
from functools import lru_cache
from typing import Any, Optional, Union

from pydantic import AnyUrl, BaseSettings, PostgresDsn, validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str = "FMTM"
    DEBUG: str = False
    LOG_LEVEL: str = "DEBUG"

    BACKEND_CORS_ORIGINS: Union[str, list[AnyUrl]] = [
        "http://localhost:8080",
        "http://localhost:8081",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, val: Union[str, list[AnyUrl]]) -> list[str]:
        """Build and validate CORS origins list."""
        if isinstance(val, str):
            return [i.strip() for i in val.split(",")]
        elif isinstance(val, list):
            return val
        raise ValueError(f"Not a valid CORS origin list: {val}")

    API_PREFIX: Optional[str] = "/"

    FMTM_DB_HOST: Optional[str] = "fmtm-db"
    FMTM_DB_USER: Optional[str] = "fmtm"
    FMTM_DB_PASSWORD: Optional[str] = "fmtm"
    FMTM_DB_NAME: Optional[str] = "fmtm"
    DB_URL: Optional[PostgresDsn]

    @validator("DB_URL", pre=True)
    def assemble_db_connection(cls, v: str, values: dict[str, Any]) -> Any:
        """Build Postgres connection from environment variables."""
        if isinstance(v, str):
            return v
        if not (user := values.get("FMTM_DB_USER")):
            raise ValueError("FMTM_DB_USER is not present in the environment")
        if not (password := values.get("FMTM_DB_PASSWORD")):
            raise ValueError("FMTM_DB_PASSWORD is not present in the environment")
        if not (host := values.get("FMTM_DB_HOST")):
            raise ValueError("FMTM_DB_HOST is not present in the environment")
        return PostgresDsn.build(
            scheme="postgresql",
            user=user,
            password=password,
            host=host,
            path=f"/{values.get('FMTM_DB_NAME') or ''}",
        )

    ODK_CENTRAL_URL: AnyUrl
    ODK_CENTRAL_USER: str
    ODK_CENTRAL_PASSWD: str

    OSM_CLIENT_ID: str
    OSM_CLIENT_SECRET: str
    OSM_URL: AnyUrl
    OSM_SCOPE: str
    OSM_LOGIN_REDIRECT_URI: AnyUrl
    OSM_SECRET_KEY: str
    OAUTHLIB_INSECURE_TRANSPORT: Optional[str] = 1

    class Config:
        """Pydantic settings config."""

        case_sensitive = True
        env_file = ".env"


@lru_cache
def get_settings():
    _settings = Settings()
    logger.info(f"Loaded settings: {_settings.dict()}")
    return _settings


settings = get_settings()
