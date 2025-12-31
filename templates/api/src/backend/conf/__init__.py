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

#### Validation ####
VALIDATED_ENV_VARS = [
    HTTP_AUTORELOAD,
    HTTP_EXPOSE_ERRORS,
    HTTP_PORT,
    LOG_LEVEL,
]

def validate() -> bool:
    return env.validate(VALIDATED_ENV_VARS)

#### Getters ####

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
