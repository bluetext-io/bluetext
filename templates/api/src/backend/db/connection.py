import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional
from psycopg_pool import AsyncConnectionPool
from sqlmodel import SQLModel, create_engine

from ..utils import log
from .. import conf

logger = log.get_logger(__name__)

_pool: Optional[AsyncConnectionPool] = None
_reconnect_task: Optional[asyncio.Task] = None
_connected = False
_last_connection_error = None
_last_error_log_time = 0

def get_conn_str() -> str:
    """Build PostgreSQL connection string from environment variables."""
    db_conf = conf.get_postgres_conf()
    return (
        f"dbname={db_conf.database} "
        f"user={db_conf.user} "
        f"password={db_conf.password} "
        f"host={db_conf.host} "
        f"port={db_conf.port}"
    )

def get_sqlalchemy_url() -> str:
    """Build SQLAlchemy URL from environment variables."""
    db_conf = conf.get_postgres_conf()
    return (
        f"postgresql+psycopg://{db_conf.user}:{db_conf.password}@"
        f"{db_conf.host}:{db_conf.port}/{db_conf.database}"
    )

async def create_pool() -> AsyncConnectionPool:
    """Create and return a new connection pool."""
    pool_conf = conf.get_postgres_pool_conf()
    pool = AsyncConnectionPool(
        conninfo=get_conn_str(),
        min_size=pool_conf.min_size,
        max_size=pool_conf.max_size,
        timeout=30.0,
        max_lifetime=3600.0,
        max_idle=600.0,
        open=False,  # Don't open in constructor to avoid deprecation warning
    )
    await pool.open()  # Open explicitly
    return pool

async def init_db() -> None:
    """Initialize database connection (non-blocking)."""
    if not conf.USE_POSTGRES:
        logger.info("PostgreSQL is disabled (USE_POSTGRES=False)")
        return

    logger.info("PostgreSQL client initialized")

async def init_connection() -> None:
    """Initialize connection with retry loop - call in background task"""
    global _reconnect_task
    _reconnect_task = asyncio.create_task(_connection_retry_loop())

async def _connection_retry_loop() -> None:
    """Retry connection loop that runs in background"""
    global _pool, _connected
    
    while not _connected:
        try:
            logger.info("Connecting to PostgreSQL...")
            _pool = await create_pool()

            # Test the connection
            async with _pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    if result and result[0] == 1:
                        logger.info("PostgreSQL connection successful")

            # Create tables using SQLModel
            await create_tables()

            _connected = True
            logger.info("PostgreSQL connection established successfully")
            
            # Start background health check
            asyncio.create_task(_monitor_connection())
            break

        except Exception as e:
            global _last_connection_error, _last_error_log_time
            _last_connection_error = str(e)
            current_time = time.time()
            
            # Log error every 10 seconds
            if current_time - _last_error_log_time >= 10:
                logger.warning(f"PostgreSQL connection failed, retrying: {e}")
                _last_error_log_time = current_time
            
            await asyncio.sleep(1)  # Wait 1 second before retry

async def create_tables() -> None:
    """Create database tables using SQLModel."""
    try:
        # Import models to register them with SQLModel
        from . import models  # noqa: F401

        # Create engine
        engine = create_engine(get_sqlalchemy_url())

        # Try to create all tables
        logger.info("Creating database tables...")
        try:
            SQLModel.metadata.create_all(engine)
            logger.info("✓ Database tables created successfully")
        except Exception as e:
            # If creation fails (e.g., incompatible schema), drop and recreate
            logger.exception(f"Failed to create tables, attempting drop and recreate: {e}")
            try:
                SQLModel.metadata.drop_all(engine)
                logger.warning("Dropped all existing tables")
                SQLModel.metadata.create_all(engine)
                logger.info("✓ Database tables recreated successfully")
            except Exception as drop_error:
                logger.exception(f"Failed to drop and recreate tables: {drop_error}")
                raise

    except ImportError as e:
        logger.warning(f"Models not found: {e}")
    except Exception as e:
        logger.exception(f"Failed to create tables: {e}")
        # Don't fail startup, just log the error
        logger.warning("Continuing without creating tables. They may need to be created manually.")

async def _ensure_connected():
    """Ensure database is connected (blocks until connected)"""
    while not _connected:
        await asyncio.sleep(0.1)  # Wait for connection

async def _monitor_connection() -> None:
    """Background task to monitor connection health."""
    global _pool, _connected

    while _pool and _connected:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            if _pool:
                async with _pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT 1")
                        await cur.fetchone()
        except Exception as e:
            logger.error(f"Database connection lost: {e}")
            _connected = False
            logger.info("Attempting to reconnect...")
            try:
                if _pool:
                    await _pool.close()
                _pool = await create_pool()
                _connected = True
                logger.info("Successfully reconnected to database")
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {reconnect_error}")
                await asyncio.sleep(10)

async def close_db() -> None:
    """Close database connection pool."""
    global _pool, _reconnect_task, _connected

    if _reconnect_task:
        _reconnect_task.cancel()
        try:
            await _reconnect_task
        except asyncio.CancelledError:
            pass
        _reconnect_task = None

    if _pool:
        await _pool.close()
        _pool = None
        _connected = False
        logger.info("Database connection pool closed")

def get_pool() -> Optional[AsyncConnectionPool]:
    """Get the current connection pool."""
    return _pool

@asynccontextmanager
async def get_connection():
    """Get a database connection from the pool.

    Usage:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users")
                results = await cur.fetchall()
    """
    await _ensure_connected()
    
    if not _pool:
        raise RuntimeError("Database pool not available")

    async with _pool.connection() as conn:
        yield conn

async def is_connected() -> bool:
    """Check if database is connected and responsive (blocking)."""
    await _ensure_connected()
    
    if not _pool:
        return False

    try:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                return result and result[0] == 1
    except Exception:
        return False

def health_check() -> dict:
    """Check if PostgreSQL connection is healthy (non-blocking for health endpoints)"""
    if not _connected:
        return {
            "connected": False, 
            "status": "connecting",
            "last_error": _last_connection_error
        }
    
    return {"connected": True, "status": "healthy"}
