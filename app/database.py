from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings
from urllib.parse import quote_plus
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{quote_plus(settings.database_username)}:"
    f"{quote_plus(settings.database_password)}"
    f"@{settings.database_hostname}:"
    f"{settings.database_port}/"
    f"{settings.database_name}"
    f"?sslmode=require"
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
