from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings
from urllib.parse import quote_plus

# Local Postgres installs (e.g. on your own machine) usually don't have
# SSL configured, while cloud providers (Render, Supabase, etc.) require it.
# Only force sslmode=require when we're NOT talking to a local database.
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

_ssl_query = (
    ""
    if settings.database_hostname in _LOCAL_HOSTS
    else "?sslmode=require"
)

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{quote_plus(settings.database_username)}:"
    f"{quote_plus(settings.database_password)}"
    f"@{settings.database_hostname}:"
    f"{settings.database_port}/"
    f"{settings.database_name}"
    f"{_ssl_query}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # automatically reconnect on stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()