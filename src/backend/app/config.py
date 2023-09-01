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

from pydantic import AnyUrl, Extra, FieldValidationInfo, PostgresDsn, field_validator
from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str = "FMTM"
    DEBUG: bool = False
    LOG_LEVEL: str = "DEBUG"

    URL_SCHEME: Optional[str] = "http"
    FRONTEND_MAIN_URL: Optional[str]
    FRONTEND_MAP_URL: Optional[str]

    EXTRA_CORS_ORIGINS: Optional[Union[str, list[AnyUrl]]] = None

    @field_validator("EXTRA_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(
        cls,
        val: Union[str, list[Url]],
        info: FieldValidationInfo,
    ) -> Union[list[str], str]:
        """Build and validate CORS origins list.

        By default, the provided frontend URLs are included in the origins list.
        If this variable used, the provided urls are appended to the list.
        """
        default_origins = []

        # Build default origins from env vars
        url_scheme = info.data.get("URL_SCHEME")
        main_url = info.data.get("URL_SCHEME")
        map_url = info.data.get("URL_SCHEME")
        if url_scheme and main_url and map_url:
            default_origins = [
                f"{url_scheme}://{main_url}",
                f"{url_scheme}://{map_url}",
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
    def assemble_db_connection(cls, v: Optional[str], info: FieldValidationInfo) -> Any:
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
        return str(pg_url)

    ODK_CENTRAL_URL: Optional[AnyUrl]
    ODK_CENTRAL_USER: Optional[str]
    ODK_CENTRAL_PASSWD: Optional[str]

    OSM_CLIENT_ID: str
    OSM_CLIENT_SECRET: str
    OSM_SECRET_KEY: str
    OSM_URL: AnyUrl = "https://www.openstreetmap.org"
    OSM_SCOPE: str = "read_prefs"
    OSM_LOGIN_REDIRECT_URI: AnyUrl = "http://127.0.0.1:8080/osmauth/"

    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra=Extra.allow
    )


@lru_cache
def get_settings():
    """Cache settings when accessed throughout app."""
    _settings = Settings()
    if _settings.DEBUG:
        print(f"Loaded settings: {_settings.dict()}")
    return _settings


settings = get_settings()
