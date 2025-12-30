"""
Database configuration with SQLAlchemy.

Designed to work with both SQLite (development) and PostgreSQL (production).
To switch databases, just change the DATABASE_URL environment variable.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

# Configure engine based on database type
# SQLite requires check_same_thread=False for FastAPI
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL or other databases
    # Convert connection string for psycopg v3 compatibility
    # Railway injects postgresql:// but psycopg3 requires postgresql+psycopg://
    connection_string = str(settings.DATABASE_URL)
    if connection_string.startswith("postgresql://"):
        connection_string = connection_string.replace("postgresql://", "postgresql+psycopg://", 1)
    
    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy session that auto-closes after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
