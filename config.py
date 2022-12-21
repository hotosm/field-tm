# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

import os
from pathlib import Path

class BaseConfig:
    """Base configuration"""
    BASE_DIR = Path(__file__).parent

    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_DATABASE_URI = os.environ.get(
    #     "DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3")
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://fmtm:fmtm@db:5432' #TODO use environmental variables here
    STATIC_FOLDER = os.environ.get(
        "PROJECTS_UPLOAD_FOLDER", os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "src", "web", "static"))
    PROJECTS_UPLOAD_FOLDER_NAME = "projects"
    QR_CODE_FOLDER_NAME = "QR_codes"


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False


class TestConfig(BaseConfig):
    """Production configuration"""
    DEBUG = True
    TESTING = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestConfig,
}
