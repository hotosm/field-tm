# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Config file for Pydantic and FastAPI, using environment variables."""

from functools import lru_cache
from typing import Any, Optional, Union

from pydantic import PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str = "FMTM"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    FMTM_DOMAIN: Optional[str]
    FMTM_DEV_PORT: Optional[str] = "7050"

    EXTRA_CORS_ORIGINS: Optional[Union[str, list[str]]] = []

    @field_validator("EXTRA_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls,
        val: Union[str, list[str]],
        info: ValidationInfo,
    ) -> Union[list[str], str]:
        """Build and validate CORS origins list.

        By default, the provided frontend URLs are included in the origins list.
        If this variable used, the provided urls are appended to the list.
        """
        default_origins = []

        # Build default origins from env vars
        url_scheme = "http" if info.data.get("DEBUG") else "https"
        local_server_port = (
            f":{info.data.get('FMTM_DEV_PORT')}" if info.data.get("DEBUG") else ""
        )
        if frontend_domain := info.data.get("FMTM_DOMAIN"):
            default_origins = [
                f"{url_scheme}://{frontend_domain}{local_server_port}",
            ]

        if val is None:
            return default_origins

        if isinstance(val, str):
            default_origins += [i.strip() for i in val.split(",")]
            return default_origins

        elif isinstance(val, list):
            default_origins += val
            return default_origins

        raise ValueError(f"Not a valid CORS origin list: {val}")

    API_PREFIX: Optional[str] = "/"

    FMTM_DB_HOST: Optional[str] = "fmtm-db"
    FMTM_DB_USER: Optional[str] = "fmtm"
    FMTM_DB_PASSWORD: Optional[str] = "fmtm"
    FMTM_DB_NAME: Optional[str] = "fmtm"

    FMTM_DB_URL: Optional[PostgresDsn] = None

    @field_validator("FMTM_DB_URL", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Build Postgres connection from environment variables."""
        if isinstance(v, str):
            return v
        pg_url = PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("FMTM_DB_USER"),
            password=info.data.get("FMTM_DB_PASSWORD"),
            host=info.data.get("FMTM_DB_HOST"),
            path=info.data.get("FMTM_DB_NAME", ""),
        )
        # Convert Url type to string
        return pg_url

    ODK_CENTRAL_URL: Optional[str] = ""
    ODK_CENTRAL_USER: Optional[str] = ""
    ODK_CENTRAL_PASSWD: Optional[str] = ""

    OSM_CLIENT_ID: str
    OSM_CLIENT_SECRET: str
    OSM_SECRET_KEY: str
    OSM_URL: str = "https://www.openstreetmap.org"
    OSM_SCOPE: str = "read_prefs"
    OSM_LOGIN_REDIRECT_URI: str = "http://127.0.0.1:7051/osmauth/"

    S3_ENDPOINT: str = "http://s3:9000"
    S3_ACCESS_KEY: Optional[str] = ""
    S3_SECRET_KEY: Optional[str] = ""
    S3_BUCKET_NAME: str = "fmtm-data"
    S3_DOWNLOAD_ROOT: Optional[str] = None

    @field_validator("S3_DOWNLOAD_ROOT", mode="before")
    @classmethod
    def configure_s3_download_root(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Set S3_DOWNLOAD_ROOT for dev setup.

        This is required, as normally S3_DOWNLOAD_ROOT is the same
        as S3_ENDPOINT, but for development we use the docker compose
        service name for S3_ENDPOINT instead.
        """
        # If set manually, pass through
        if isinstance(v, str):
            return v
        # For dev setup
        dev_port = info.data.get("FMTM_DEV_PORT")
        if s3_endpoint := info.data.get("S3_ENDPOINT") == "http://s3:9000":
            return f"http://s3.fmtm.localhost:{dev_port}"
        # Else set to value of S3_ENDPOINT
        return s3_endpoint

    UNDERPASS_API_URL: str = "https://api-prod.raw-data.hotosm.org/v1/"
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra="allow"
    )


@lru_cache
def get_settings():
    """Cache settings when accessed throughout app."""
    _settings = Settings()
    if _settings.DEBUG:
        print(f"Loaded settings: {_settings.model_dump()}")
    return _settings


settings = get_settings()
