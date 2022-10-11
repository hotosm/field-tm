import os
from pathlib import Path


class BaseConfig:
    """Base configuration"""
    BASE_DIR = Path(__file__).parent

    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3")


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
