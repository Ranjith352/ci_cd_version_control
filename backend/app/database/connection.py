import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi import HTTPException, status
from backend.app.config import DATABASE_URL, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB

logger = logging.getLogger("backend.database")

# Create SQLAlchemy engine targeting PostgreSQL database data_engineering
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={"connect_timeout": 5},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize PostgreSQL engine: {e}")
    engine = None
    SessionLocal = None


def get_db_session():
    """FastAPI dependency yielding a PostgreSQL database session."""
    if SessionLocal is None or engine is None:
        logger.error("Database SessionLocal is uninitialized.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PostgreSQL database unavailable at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        )

    session: Session = SessionLocal()
    try:
        # Ping connection to verify active status
        session.execute(text("SELECT 1"))
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PostgreSQL database error: Could not reach {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        )
    finally:
        session.close()
