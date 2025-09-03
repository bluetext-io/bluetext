import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from psycopg_pool import AsyncConnectionPool
from sqlmodel import SQLModel, create_engine

from ..utils import log
from .. import conf

logger = log.get_logger(__name__)

_pool: Optional[AsyncConnectionPool] = None
_reconnect_task: Optional[asyncio.Task] = None

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
    """Initialize database connection pool and create tables.

    Retries connection every 10 seconds if PostgreSQL is unavailable.
    """
    global _pool, _reconnect_task

    if not conf.USE_POSTGRES:
        logger.info("PostgreSQL is disabled (USE_POSTGRES=False)")
        return

    retry_count = 0
    while True:
        try:
            logger.info("Connecting to PostgreSQL...")
            _pool = await create_pool()

            # Test the connection
            async with _pool.connection() as conn:
                # Test connection
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    if result and result[0] == 1:
                        logger.info("PostgreSQL connection successful")

            # Create tables using SQLModel
            await create_tables()

            # Start background health check
            _reconnect_task = asyncio.create_task(_monitor_connection())
            break

        except Exception as e:
            retry_count += 1
            if retry_count == 1:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
            if retry_count % 6 == 0:  # Log every minute
                logger.warning(f"Still trying to connect to PostgreSQL... (attempt {retry_count})")
            await asyncio.sleep(10)

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

async def _monitor_connection() -> None:
    """Background task to monitor connection health."""
    global _pool

    while _pool:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            if _pool:
                async with _pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT 1")
                        await cur.fetchone()
        except Exception as e:
            logger.error(f"Database connection lost: {e}")
            logger.info("Attempting to reconnect...")
            try:
                if _pool:
                    await _pool.close()
                _pool = await create_pool()
                logger.info("Successfully reconnected to database")
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {reconnect_error}")
                await asyncio.sleep(10)

async def close_db() -> None:
    """Close database connection pool."""
    global _pool, _reconnect_task

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
    if not _pool:
        if conf.USE_POSTGRES:
            raise RuntimeError("Database pool not initialized. Call init_db() first.")
        else:
            raise RuntimeError("PostgreSQL is disabled (USE_POSTGRES=False)")

    async with _pool.connection() as conn:
        yield conn

async def is_connected() -> bool:
    """Check if database is connected and responsive."""
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
