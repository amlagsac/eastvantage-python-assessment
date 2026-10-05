from collections.abc import Generator
import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


# The starting point that all database table models are built from
class Base(DeclarativeBase):
    pass


# Extra options for connecting to the database, filled in below if needed
connect_args: dict[str, bool] = {}
engine_kwargs: dict = {}

# Checking if the database URL is a SQLite URL from the environment variables
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if settings.DATABASE_URL in {"sqlite://", "sqlite:///:memory:"}:
        engine_kwargs["poolclass"] = StaticPool

# Creates the main connection to the database using the URL from the settings
engine: Engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)
# Creates a factory for making database sessions. Changes are only saved when
# we say so (no auto-saving).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Log only the database dialect; connection URLs can contain credentials.
logger.info("Database engine configured dialect=%s", engine.dialect.name)


def get_db() -> Generator[Session, None, None]:
    # Opens a new database session for a request
    db = SessionLocal()
    # Debug-level lifecycle logs help trace dependency-scoped database sessions.
    logger.debug("Opened database session")
    try:
        # Hands the session over to whoever needs it
        yield db
    finally:
        # Always closes the session when the request is done, even if something went wrong
        db.close()
        logger.debug("Closed database session")