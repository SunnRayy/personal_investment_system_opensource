# File path: src/database/base.py
"""
Database base configuration and session management.

Provides SQLAlchemy Base class, engine creation, and session management
for the Personal Investment System database.
"""

import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Create declarative base for all ORM models
Base = declarative_base()

# Global engine and session factory (initialized once)
_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def get_engine(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Get or create the SQLAlchemy engine.
    
    Args:
        database_url: Database connection string. If None, uses default SQLite path.
        echo: If True, log all SQL statements (useful for debugging).
    
    Returns:
        SQLAlchemy Engine instance.
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    # Default to SQLite in data/ directory
    if database_url is None:
        # Get project root (3 levels up from this file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Use DB_PATH from environment if set, otherwise use default
        db_path_env = os.getenv('DB_PATH')
        if db_path_env:
            # Support both absolute and relative paths
            if os.path.isabs(db_path_env):
                db_path = db_path_env
            else:
                db_path = os.path.join(project_root, db_path_env)
        else:
            db_path = os.path.join(project_root, 'data', 'investment_system.db')

        database_url = f'sqlite:///{db_path}'
        
        # Auto-initialize if database doesn't exist (Clean Environment support)
        db_exists = os.path.exists(db_path)
        if not db_exists:
            logger.info(f"🆕 Database not found at {db_path}. Will auto-initialize fresh schema.")
        else:
            logger.info(f"Using database: {db_path}")
    
    # Create engine with SQLite-specific settings
    if database_url.startswith('sqlite'):
        # Enable foreign key constraints for SQLite
        _engine = create_engine(
            database_url,
            echo=echo,
            connect_args={'check_same_thread': False},  # Allow multi-threaded access
            poolclass=StaticPool,  # Single connection pool for SQLite
        )
        
        # Enable foreign keys and WAL mode for SQLite
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")  # Enforce foreign key constraints
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for crash protection
            cursor.close()
    else:
        # PostgreSQL or other database
        _engine = create_engine(database_url, echo=echo, pool_pre_ping=True)
    
    logger.info(f"Database engine created: {database_url.split('//')[0]}")
    return _engine


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        SQLAlchemy Session instance.
    
    Usage:
        ```python
        session = get_session()
        try:
            # Perform database operations
            session.add(transaction)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
        ```
    """
    global _SessionFactory
    
    if _SessionFactory is None:
        engine = get_engine()
        
        # Auto-create tables if database is new (Clean Environment support)
        # This ensures the system can start from scratch without manual init
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        if not existing_tables:
            logger.info("🆕 Empty database detected. Auto-initializing schema...")
            Base.metadata.create_all(engine)
            logger.info("✅ Database schema auto-initialized successfully")
        
        _SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    
    return _SessionFactory()


def init_database(database_url: Optional[str] = None, drop_existing: bool = False) -> None:
    """
    Initialize the database by creating all tables.
    
    Args:
        database_url: Database connection string. If None, uses default SQLite path.
        drop_existing: If True, drop all existing tables before creating (DANGEROUS).
    
    Raises:
        RuntimeError: If database initialization fails.
    """
    try:
        engine = get_engine(database_url)
        
        if drop_existing:
            logger.warning("⚠️  Dropping all existing tables...")
            Base.metadata.drop_all(engine)
        
        # Create all tables defined in ORM models
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        logger.info(f"✅ Database initialized successfully with {len(table_names)} tables:")
        for table in table_names:
            logger.info(f"  - {table}")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise RuntimeError(f"Failed to initialize database: {e}")


def reset_engine() -> None:
    """
    Reset the global engine and session factory.
    
    Useful for testing or when switching databases.
    """
    global _engine, _SessionFactory
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
    
    _SessionFactory = None
    logger.info("Database engine reset")
