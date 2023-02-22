"""Config file for Pydantic and FastAPI, using environment variables."""

from typing import Any, Optional, Union

from pydantic import AnyUrl, BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str = "FMTM"
    DEBUG: str = False
    LOG_LEVEL: str = "INFO"

    BACKEND_CORS_ORIGINS: list[AnyUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> Union[list[str], str]:
        """Build and validate CORS origins list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    FMTM_DB_HOST: Optional[str]
    FMTM_DB_USER: Optional[str]
    FMTM_DB_PASSWORD: Optional[str]
    FMTM_DB_NAME: Optional[str]
    DB_URL: PostgresDsn = None

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
            scheme="postgres",
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

    class Config:
        """Pydantic settings config."""

        case_sensitive = True


settings = Settings()
