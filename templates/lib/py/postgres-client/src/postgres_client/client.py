import asyncio
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from contextlib import asynccontextmanager

from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel # noqa

logger = logging.getLogger(__name__)


@dataclass
class PostgresConf:
    """PostgreSQL configuration"""
    database: str
    user: str
    password: str
    host: str
    port: int

    def get_connection_string(self) -> str:
        """Get psycopg connection string"""
        return (
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"host={self.host} "
            f"port={self.port}"
        )

    def get_sqlalchemy_url(self) -> str:
        """Get SQLAlchemy URL for SQLModel"""
        return (
            f"postgresql+psycopg://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


@dataclass
class PostgresPoolConf:
    """PostgreSQL connection pool configuration"""
    min_size: int = 1
    max_size: int = 10


class PostgresClient:
    """
    Lightweight PostgreSQL client for connection management.

    Handles connection pooling, retries, and provides the SQLAlchemy engine
    for SQLModel operations.
    """

    def __init__(self, config: PostgresConf, pool_config: Optional[PostgresPoolConf] = None):
        self._config = config
        self._pool_config = pool_config or PostgresPoolConf()
        self._pool: Optional[AsyncConnectionPool] = None
        self._engine = None
        self._initialized = False
        self._connected = False
        self._connection_task = None
        self._monitor_task = None
        self._last_connection_error = None
        self._last_error_log_time = 0

    async def initialize(self):
        """Initialize the PostgreSQL client"""
        if not self._config:
            raise ValueError("PostgresConf required")

        # Create SQLAlchemy engine for SQLModel
        self._engine = create_async_engine(self._config.get_sqlalchemy_url())

        self._initialized = True
        logger.info("PostgreSQL client initialized")

    async def init_connection(self):
        """Initialize connection with retry loop - call in background task"""
        if not self._initialized:
            return

        self._connection_task = asyncio.create_task(self._connection_retry_loop())

    async def _connection_retry_loop(self):
        """Retry connection loop that runs in background"""
        while not self._connected:
            try:
                logger.info("Connecting to PostgreSQL...")
                self._pool = await self._create_pool()

                # Test the connection
                async with self._pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT 1")
                        result = await cur.fetchone()
                        if result and result[0] == 1:
                            logger.info("PostgreSQL connection test successful")

                self._connected = True
                logger.info("PostgreSQL connection established successfully")

                # Start background health monitor
                self._monitor_task = asyncio.create_task(self._monitor_connection())
                break

            except Exception as e:
                self._last_connection_error = str(e)
                current_time = time.time()

                # Log error every 10 seconds
                if current_time - self._last_error_log_time >= 10:
                    logger.warning(f"PostgreSQL connection failed, retrying: {e}")
                    self._last_error_log_time = current_time

                await asyncio.sleep(1)  # Wait 1 second before retry

    async def _create_pool(self) -> AsyncConnectionPool:
        """Create and return a new connection pool"""
        pool = AsyncConnectionPool(
            conninfo=self._config.get_connection_string(),
            min_size=self._pool_config.min_size,
            max_size=self._pool_config.max_size,
            timeout=30.0,
            max_lifetime=3600.0,
            max_idle=600.0,
            open=False,  # Don't open in constructor to avoid deprecation warning
        )
        await pool.open()  # Open explicitly
        return pool

    async def create_tables(self, metadata):
        """Create database tables using provided SQLModel metadata

        Args:
            metadata: SQLModel.metadata object with registered tables
        """
        try:
            # Try to create all tables
            logger.info("Creating database tables...")
            try:
                async with self._engine.begin() as conn:
                    await conn.run_sync(metadata.create_all)
                logger.info("Database tables created successfully")
            except Exception as e:
                # If creation fails (e.g., incompatible schema), drop and recreate
                logger.exception(f"Failed to create tables, attempting drop and recreate: {e}")
                try:
                    async with self._engine.begin() as conn:
                        await conn.run_sync(metadata.drop_all)
                        logger.warning("Dropped all existing tables")
                        await conn.run_sync(metadata.create_all)
                    logger.info("Database tables recreated successfully")
                except Exception as drop_error:
                    logger.exception(f"Failed to drop and recreate tables: {drop_error}")
                    raise
        except Exception as e:
            logger.exception(f"Failed to create tables: {e}")
            # Don't fail startup, just log the error
            logger.warning("Continuing without creating tables. They may need to be created manually.")

    async def _monitor_connection(self):
        """Background task to monitor connection health"""
        while self._pool and self._connected:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                if self._pool:
                    async with self._pool.connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("SELECT 1")
                            await cur.fetchone()
            except Exception as e:
                logger.error(f"Database connection lost: {e}")
                self._connected = False
                logger.info("Attempting to reconnect...")
                try:
                    if self._pool:
                        await self._pool.close()
                    self._pool = await self._create_pool()
                    self._connected = True
                    logger.info("Successfully reconnected to database")
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect: {reconnect_error}")
                    await asyncio.sleep(10)

    def _ensure_initialized(self):
        """Ensure client is initialized"""
        if not self._initialized:
            raise RuntimeError("PostgreSQL client not initialized")

    async def _ensure_connected(self):
        """Ensure client is connected (blocks until connected)"""
        self._ensure_initialized()
        while not self._connected:
            await asyncio.sleep(0.1)  # Wait for connection

    async def close(self):
        """Close the PostgreSQL client"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass
            self._connection_task = None

        if self._pool:
            await self._pool.close()
            self._pool = None
            self._connected = False
            self._initialized = False
            logger.info("PostgreSQL client closed")

    def get_engine(self):
        """Get SQLAlchemy engine for SQLModel operations"""
        self._ensure_initialized()
        return self._engine

    def get_pool(self) -> Optional[AsyncConnectionPool]:
        """Get the current connection pool (for advanced/raw SQL usage)"""
        return self._pool

    @asynccontextmanager
    async def get_connection(self):
        """
        Get a raw database connection from the pool.
        For SQLModel operations, use get_engine() instead.

        Usage:
            async with client.get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM users")
                    results = await cur.fetchall()
        """
        await self._ensure_connected()

        if not self._pool:
            raise RuntimeError("Database pool not available")

        async with self._pool.connection() as conn:
            yield conn

    @asynccontextmanager
    async def get_session(self):
        """
        Get an AsyncSession for SQLModel operations with automatic transaction management.

        Usage:
            async with client.get_session() as session:
                user = User(name="John")
                session.add(user)
                # session.commit() called automatically on success
                # session.rollback() called automatically on exception
        """
        self._ensure_initialized()

        async with AsyncSession(self._engine) as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def is_connected(self) -> bool:
        """Check if database is connected and responsive (blocking)"""
        await self._ensure_connected()

        if not self._pool:
            return False

        try:
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    return result and result[0] == 1
        except Exception:
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check if PostgreSQL connection is healthy (non-blocking for health endpoints)"""
        if not self._initialized:
            return {"connected": False, "status": "not_initialized"}

        if not self._connected:
            return {
                "connected": False,
                "status": "connecting",
                "last_error": self._last_connection_error
            }

        return {"connected": True, "status": "healthy"}