import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
import psycopg

load_dotenv()

logger = logging.getLogger("aquaslick.database")

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://postgres:password@localhost:5432/aquaslick"
)

# Standardize dialect for psycopg v3
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DB_CONNECTION_ERRORS = (OperationalError, psycopg.OperationalError)

def is_db_reachable() -> bool:
    """Checks database connection without masking code or schema bugs."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except DB_CONNECTION_ERRORS as exc:
        logger.warning("PostgreSQL unreachable. Fallback mode active: %s", exc)
        return False