from pydantic import BaseModel

from .utils import env, log
from .utils.env import EnvVarSpec

logger = log.get_logger(__name__)

# Set to False if you don't want to use PostgreSQL
# When False, all database functionality will be disabled
USE_POSTGRES = False

# Set to True if you want to use Couchbase
# When False, couchbase client will not be initialized
USE_COUCHBASE = False

#### Types ####

class HttpServerConf(BaseModel):
    host: str
    port: int
    autoreload: bool

class PostgresConf(BaseModel):
    database: str
    user: str
    password: str
    host: str
    port: int

class PostgresPoolConf(BaseModel):
    min_size: int
    max_size: int

#### Env Vars ####

## Logging ##

LOG_LEVEL = EnvVarSpec(id="LOG_LEVEL", default="INFO")

## HTTP ##

HTTP_HOST = EnvVarSpec(id="HTTP_HOST", default="0.0.0.0")

HTTP_PORT = EnvVarSpec(id="HTTP_PORT", default="8000")

HTTP_AUTORELOAD = EnvVarSpec(
    id="HTTP_AUTORELOAD",
    parse=lambda x: x.lower() == "true",
    default="false",
    type=(bool, ...),
)

## PostgreSQL ##

POSTGRES_DB = EnvVarSpec(
    id="POSTGRES_DB",
    default="postgres"
)

POSTGRES_USER = EnvVarSpec(
    id="POSTGRES_USER",
    default="postgres"
)

POSTGRES_PASSWORD = EnvVarSpec(
    id="POSTGRES_PASSWORD",
    default="postgres",
    is_secret=True
)

POSTGRES_HOST = EnvVarSpec(
    id="POSTGRES_HOST",
    default="postgres"
)

POSTGRES_PORT = EnvVarSpec(
    id="POSTGRES_PORT",
    parse=int,
    default="5432",
    type=(int, ...)
)

POSTGRES_POOL_MIN = EnvVarSpec(
    id="POSTGRES_POOL_MIN",
    parse=int,
    default="1",
    type=(int, ...)
)

POSTGRES_POOL_MAX = EnvVarSpec(
    id="POSTGRES_POOL_MAX",
    parse=int,
    default="10",
    type=(int, ...)
)

## Couchbase ##

COUCHBASE_HOST = EnvVarSpec(
    id="COUCHBASE_HOST",
    default="couchbase"
)

COUCHBASE_USERNAME = EnvVarSpec(
    id="COUCHBASE_USERNAME",
    default="user"
)

COUCHBASE_PASSWORD = EnvVarSpec(
    id="COUCHBASE_PASSWORD",
    default="password",
    is_secret=True
)

COUCHBASE_BUCKET = EnvVarSpec(
    id="COUCHBASE_BUCKET",
    default="main"
)

COUCHBASE_PROTOCOL = EnvVarSpec(
    id="COUCHBASE_PROTOCOL",
    default="couchbase"
)

#### Validation ####

def validate() -> bool:
    env_vars = [
        LOG_LEVEL,
        HTTP_PORT,
        HTTP_AUTORELOAD,
    ]

    # Only validate PostgreSQL vars if USE_POSTGRES is True
    if USE_POSTGRES:
        env_vars.extend([
            POSTGRES_DB,
            POSTGRES_USER,
            POSTGRES_PASSWORD,
            POSTGRES_HOST,
            POSTGRES_PORT,
            POSTGRES_POOL_MIN,
            POSTGRES_POOL_MAX,
        ])

    # Only validate Couchbase vars if USE_COUCHBASE is True
    if USE_COUCHBASE:
        env_vars.extend([
            COUCHBASE_HOST,
            COUCHBASE_USERNAME,
            COUCHBASE_PASSWORD,
            COUCHBASE_BUCKET,
            COUCHBASE_PROTOCOL,
        ])

    return env.validate(env_vars)

#### Getters ####

def get_log_level() -> str:
    return env.parse(LOG_LEVEL)

def get_http_conf() -> HttpServerConf:
    return HttpServerConf(
        host=env.parse(HTTP_HOST),
        port=env.parse(HTTP_PORT),
        autoreload=env.parse(HTTP_AUTORELOAD),
    )

def get_postgres_conf() -> PostgresConf:
    """Get PostgreSQL connection configuration.
    Only call this if USE_POSTGRES is True.
    """
    return PostgresConf(
        database=env.parse(POSTGRES_DB),
        user=env.parse(POSTGRES_USER),
        password=env.parse(POSTGRES_PASSWORD),
        host=env.parse(POSTGRES_HOST),
        port=env.parse(POSTGRES_PORT),
    )

def get_postgres_pool_conf() -> PostgresPoolConf:
    """Get PostgreSQL connection pool configuration.
    Only call this if USE_POSTGRES is True.
    """
    return PostgresPoolConf(
        min_size=env.parse(POSTGRES_POOL_MIN),
        max_size=env.parse(POSTGRES_POOL_MAX),
    )

def get_couchbase_conf():
    """Get Couchbase connection configuration.
    Only call this if USE_COUCHBASE is True.
    """
    # Import here to avoid circular dependency
    from .clients.couchbase import CouchbaseConf

    return CouchbaseConf(
        host=env.parse(COUCHBASE_HOST),
        username=env.parse(COUCHBASE_USERNAME),
        password=env.parse(COUCHBASE_PASSWORD),
        bucket=env.parse(COUCHBASE_BUCKET),
        protocol=env.parse(COUCHBASE_PROTOCOL),
    )
