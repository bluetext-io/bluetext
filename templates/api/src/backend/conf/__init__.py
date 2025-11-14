from pydantic import BaseModel

from ..utils import auth, env, log
from ..utils.env import EnvVarSpec

logger = log.get_logger(__name__)

# Set to True to enable authentication
USE_AUTH = False

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
## NOTE: PostgreSQL configuration is added dynamically by the add-postgres-client script.
## When added, it creates src/backend/conf/postgres.py with env var definitions.

## Twilio ##
## NOTE: Twilio configuration is added dynamically by the add-twilio-client script.
## When added, it creates src/backend/conf/twilio.py with env var definitions.

#### Validation ####
VALIDATED_ENV_VARS = [
    HTTP_AUTORELOAD,
    HTTP_EXPOSE_ERRORS,
    HTTP_PORT,
    LOG_LEVEL,
]


# Only validate auth vars if USE_AUTH is True
if USE_AUTH:
    VALIDATED_ENV_VARS.extend([
        AUTH_OIDC_JWK_URL,
        AUTH_OIDC_AUDIENCE,
        AUTH_OIDC_ISSUER,
    ])

def validate() -> bool:
    return env.validate(VALIDATED_ENV_VARS)

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
