from pydantic import BaseModel

from .utils import auth, env, log
from .utils.env import EnvVarSpec

logger = log.get_logger(__name__)

# Set to True to enable authentication
USE_AUTH = False

# Set to False if you don't want to use PostgreSQL
# When False, all database functionality will be disabled
USE_POSTGRES = False

# Set to True if you want to use Couchbase
# When False, couchbase client will not be initialized
USE_COUCHBASE = False

# Set to True to auto-create Couchbase buckets, scopes, and collections
# When False, will throw errors if resources don't exist
COUCHBASE_AUTO_MIGRATE = False

# Set to True to enable Temporal
USE_TEMPORAL = False

# Set to True to enable Twilio SMS functionality
USE_TWILIO = False

#### Types ####

class HttpServerConf(BaseModel):
    host: str
    port: int
    autoreload: bool

#### Env Vars ####

## Auth ##

AUTH_OIDC_JWK_URL = EnvVarSpec(id="AUTH_OIDC_JWK_URL", is_optional=True)
AUTH_OIDC_AUDIENCE = EnvVarSpec(id="AUTH_OIDC_AUDIENCE", is_optional=True)
AUTH_OIDC_ISSUER = EnvVarSpec(id="AUTH_OIDC_ISSUER", is_optional=True)

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

HTTP_EXPOSE_ERRORS = EnvVarSpec(
    id="HTTP_EXPOSE_ERRORS",
    default="false",
    parse=lambda x: x.lower() == "true",
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

## Temporal ##

TEMPORAL_HOST = EnvVarSpec(
    id="TEMPORAL_HOST",
    default="temporal"
)

TEMPORAL_PORT = EnvVarSpec(
    id="TEMPORAL_PORT",
    parse=int,
    default="7233",
    type=(int, ...)
)

TEMPORAL_NAMESPACE = EnvVarSpec(
    id="TEMPORAL_NAMESPACE",
    default="default"
)

TEMPORAL_TASK_QUEUE = EnvVarSpec(
    id="TEMPORAL_TASK_QUEUE",
    default="main-task-queue"
)

## Twilio ##

TWILIO_ACCOUNT_SID = EnvVarSpec(
    id="TWILIO_ACCOUNT_SID",
    is_optional=True
)

TWILIO_AUTH_TOKEN = EnvVarSpec(
    id="TWILIO_AUTH_TOKEN",
    is_optional=True,
    is_secret=True
)

TWILIO_FROM_PHONE_NUMBER = EnvVarSpec(
    id="TWILIO_FROM_PHONE_NUMBER",
    is_optional=True
)

#### Validation ####

def validate() -> bool:
    env_vars = [
        HTTP_AUTORELOAD,
        HTTP_EXPOSE_ERRORS,
        HTTP_PORT,
        LOG_LEVEL,
    ]

    # Only validate auth vars if USE_AUTH is True
    if USE_AUTH:
        env_vars.extend([
            AUTH_OIDC_JWK_URL,
            AUTH_OIDC_AUDIENCE,
            AUTH_OIDC_ISSUER,
        ])

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

    # Only validate Temporal vars if USE_TEMPORAL is True
    if USE_TEMPORAL:
        env_vars.extend([
            TEMPORAL_HOST,
            TEMPORAL_PORT,
            TEMPORAL_NAMESPACE,
            TEMPORAL_TASK_QUEUE,
        ])

    # Only validate Twilio vars if USE_TWILIO is True
    if USE_TWILIO:
        env_vars.extend([
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_FROM_PHONE_NUMBER,
        ])

    return env.validate(env_vars)

#### Getters ####

def get_auth_config() -> auth.AuthClientConfig:
    """Get authentication configuration."""
    return auth.AuthClientConfig(
        jwk_url=env.parse(AUTH_OIDC_JWK_URL),
        audience=env.parse(AUTH_OIDC_AUDIENCE),
        issuer=env.parse(AUTH_OIDC_ISSUER),
    )

def get_http_expose_errors() -> str:
    return env.parse(HTTP_EXPOSE_ERRORS)

def get_log_level() -> str:
    return env.parse(LOG_LEVEL)

def get_http_conf() -> HttpServerConf:
    return HttpServerConf(
        host=env.parse(HTTP_HOST),
        port=env.parse(HTTP_PORT),
        autoreload=env.parse(HTTP_AUTORELOAD),
    )

def get_postgres_conf():
    """Get PostgreSQL connection configuration."""
    # Import here to avoid circular dependency
    from .clients.postgres import PostgresConf
    
    return PostgresConf(
        database=env.parse(POSTGRES_DB),
        user=env.parse(POSTGRES_USER),
        password=env.parse(POSTGRES_PASSWORD),
        host=env.parse(POSTGRES_HOST),
        port=env.parse(POSTGRES_PORT),
    )

def get_postgres_pool_conf():
    """Get PostgreSQL connection pool configuration."""
    # Import here to avoid circular dependency
    from .clients.postgres import PostgresPoolConf
    
    return PostgresPoolConf(
        min_size=env.parse(POSTGRES_POOL_MIN),
        max_size=env.parse(POSTGRES_POOL_MAX),
    )

def get_couchbase_conf():
    """Get Couchbase connection configuration."""
    # Import here to avoid circular dependency
    from .clients.couchbase import CouchbaseConf

    return CouchbaseConf(
        host=env.parse(COUCHBASE_HOST),
        username=env.parse(COUCHBASE_USERNAME),
        password=env.parse(COUCHBASE_PASSWORD),
        bucket=env.parse(COUCHBASE_BUCKET),
        protocol=env.parse(COUCHBASE_PROTOCOL),
    )

def get_temporal_conf():
    """Get Temporal connection configuration."""
    # Import here to avoid circular dependency
    from .clients.temporal import TemporalConf

    return TemporalConf(
        host=env.parse(TEMPORAL_HOST),
        port=env.parse(TEMPORAL_PORT),
        namespace=env.parse(TEMPORAL_NAMESPACE),
        task_queue=env.parse(TEMPORAL_TASK_QUEUE),
    )

def get_twilio_conf():
    """Get Twilio configuration."""
    # Import here to avoid circular dependency
    from .clients.twilio import TwilioConf

    return TwilioConf(
        account_sid=env.parse(TWILIO_ACCOUNT_SID),
        auth_token=env.parse(TWILIO_AUTH_TOKEN),
        from_phone_number=env.parse(TWILIO_FROM_PHONE_NUMBER),
    )
