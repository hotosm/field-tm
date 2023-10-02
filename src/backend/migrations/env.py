"""Main alembic migrations file."""

from logging import getLogger
from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.db.db_models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.FMTM_DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
exclude_tables = config.get_section("alembic:exclude").get("tables", "").split(",")
log = getLogger(__name__)


def include_object(object, name, type_, reflected, compare_to):
    """Ignore our excluded tables in the autogen sweep."""
    if type_ == "table" and name in exclude_tables:
        return False
    else:
        return alembic_helpers.include_object(
            object, name, type_, reflected, compare_to
        )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    log.info("Running offline migrations")

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        include_object=include_object,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
    log.info("Complete offline migrations")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    log.info("Running online migrations")

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            include_object=include_object,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    log.info("Complete online migrations")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
