# Template Configuration File
# This file contains all configuration options for both PostgreSQL and Couchbase
# Uncomment the sections you need based on your database choice

import os
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# ENVIRONMENT VARIABLE UTILITIES
# =============================================================================

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Get environment variable with optional default and validation.

    Args:
        key: Environment variable name
        default: Default value if not set
        required: If True, raise error if not found and no default

    Returns:
        Environment variable value

    Raises:
        ValueError: If required=True and variable not found
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


# =============================================================================
# CONFIGURATION MODELS
# =============================================================================

class HttpServerConfig(BaseModel):
    """HTTP server configuration"""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on changes")


class PostgresConfig(BaseModel):
    """PostgreSQL database configuration"""
    host: str = Field(description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    database: str = Field(description="Database name")
    user: str = Field(description="Database user")
    password: str = Field(description="Database password")

    # Connection pool settings
    pool_min_size: int = Field(default=1, description="Minimum pool connections")
    pool_max_size: int = Field(default=10, description="Maximum pool connections")

    def get_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        return (
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"host={self.host} "
            f"port={self.port}"
        )

    def get_sqlalchemy_url(self) -> str:
        """Build SQLAlchemy URL"""
        return (
            f"postgresql+psycopg://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


class CouchbaseConfig(BaseModel):
    """Couchbase database configuration"""
    host: str = Field(description="Couchbase host")
    username: str = Field(description="Couchbase username")
    password: str = Field(description="Couchbase password")
    bucket: str = Field(description="Default bucket name")
    protocol: str = Field(default="couchbase", description="Connection protocol (couchbase/couchbases)")

    def get_connection_url(self) -> str:
        """Build Couchbase connection URL"""
        return f"{self.protocol}://{self.host}"


# =============================================================================
# CONFIGURATION FACTORY
# =============================================================================

class Settings:
    """
    Main settings class that loads configuration from environment variables.

    USAGE:
    1. Copy this file to your project
    2. Uncomment the database configuration you need
    3. Set the corresponding environment variables
    4. Use get_*_config() methods to access configuration
    """

    def __init__(self):
        """Initialize settings from environment variables"""
        pass

    def get_http_config(self) -> HttpServerConfig:
        """Get HTTP server configuration from environment"""
        return HttpServerConfig(
            host=get_env_var("HTTP_HOST", "0.0.0.0"),
            port=int(get_env_var("HTTP_PORT", "8000")),
            reload=get_env_var("HTTP_RELOAD", "false").lower() == "true"
        )

    # POSTGRESQL CONFIGURATION - Uncomment to use
    # def get_postgres_config(self) -> PostgresConfig:
    #     """Get PostgreSQL configuration from environment"""
    #     return PostgresConfig(
    #         host=get_env_var("POSTGRES_HOST", required=True),
    #         port=int(get_env_var("POSTGRES_PORT", "5432")),
    #         database=get_env_var("POSTGRES_DB", required=True),
    #         user=get_env_var("POSTGRES_USER", required=True),
    #         password=get_env_var("POSTGRES_PASSWORD", required=True),
    #         pool_min_size=int(get_env_var("POSTGRES_POOL_MIN", "1")),
    #         pool_max_size=int(get_env_var("POSTGRES_POOL_MAX", "10"))
    #     )

    # COUCHBASE CONFIGURATION - Uncomment to use
    # def get_couchbase_config(self) -> CouchbaseConfig:
    #     """Get Couchbase configuration from environment"""
    #     return CouchbaseConfig(
    #         host=get_env_var("COUCHBASE_HOST", required=True),
    #         username=get_env_var("COUCHBASE_USERNAME", required=True),
    #         password=get_env_var("COUCHBASE_PASSWORD", required=True),
    #         bucket=get_env_var("COUCHBASE_BUCKET", required=True),
    #         protocol=get_env_var("COUCHBASE_PROTOCOL", "couchbase")
    #     )


# Global settings instance
settings = Settings()


# =============================================================================
# ENVIRONMENT VARIABLES REFERENCE
# =============================================================================
"""
REQUIRED ENVIRONMENT VARIABLES:

HTTP Server (always required):
- HTTP_HOST (default: 0.0.0.0)
- HTTP_PORT (default: 8000)
- HTTP_RELOAD (default: false)

PostgreSQL (uncomment postgres_config to require):
- POSTGRES_HOST
- POSTGRES_PORT (default: 5432)
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_POOL_MIN (default: 1)
- POSTGRES_POOL_MAX (default: 10)

Couchbase (uncomment couchbase_config to require):
- COUCHBASE_HOST
- COUCHBASE_USERNAME
- COUCHBASE_PASSWORD
- COUCHBASE_BUCKET
- COUCHBASE_PROTOCOL (default: couchbase)
"""
