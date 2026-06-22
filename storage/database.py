"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv
from findmydos.storage.models import Base

# Load environment variables
load_dotenv()

def get_engine():
    """
    Create and return a SQLAlchemy engine based on environment configuration.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    database_url = os.environ.get(
        'DATABASE_URL',
        'sqlite:///findmydos.db'
    )

    # Special handling for SQLite to allow multiple connections
    if database_url.startswith('sqlite'):
        engine = create_engine(
            database_url,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=os.environ.get('SQL_ECHO', 'False').lower() == 'true'
        )
    else:
        engine = create_engine(
            database_url,
            echo=os.environ.get('SQL_ECHO', 'False').lower() == 'true'
        )

    return engine

def get_session_factory():
    """
    Create and return a session factory bound to the engine.

    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    engine = get_engine()
    return sessionmaker(bind=engine)

def get_scoped_session():
    """
    Create and return a scoped session for thread-safe database access.

    Returns:
        scoped_session: Thread-safe SQLAlchemy session
    """
    session_factory = get_session_factory()
    return scoped_session(session_factory)

def init_db():
    """
    Initialize the database by creating all tables.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)