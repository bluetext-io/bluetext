from pydantic import BaseModel

from .utils import env, log
from .utils.env import EnvVarSpec

logger = log.get_logger(__name__)

#### Types ####

class HttpServerConf(BaseModel):
    host: str
    port: int
    debug: bool
    autoreload: bool

class CouchbaseConf(BaseModel):
    url: str
    bucket: str
    username: str
    password: str
    scope: str = "_default"

#### Env Vars ####

## Logging ##

LOG_LEVEL = EnvVarSpec(id="LOG_LEVEL", default="INFO")

## HTTP ##

HTTP_HOST = EnvVarSpec(id="HTTP_HOST", default="0.0.0.0")

HTTP_PORT = EnvVarSpec(id="HTTP_PORT", default="8000")

HTTP_DEBUG = EnvVarSpec(
    id="HTTP_DEBUG",
    parse=lambda x: x.lower() == "true",
    default="false",
    type=(bool, ...),
)

HTTP_AUTORELOAD = EnvVarSpec(
    id="HTTP_AUTORELOAD",
    parse=lambda x: x.lower() == "true",
    default="false",
    type=(bool, ...),
)

## Opper ##

OPPER_API_KEY = EnvVarSpec(id="OPPER_API_KEY", is_secret=True)

## Couchbase ##

COUCHBASE_BUCKET   = EnvVarSpec(id="COUCHBASE_BUCKET")
COUCHBASE_PASSWORD = EnvVarSpec(id="COUCHBASE_PASSWORD", is_secret=True)
COUCHBASE_SCOPE    = EnvVarSpec(id="COUCHBASE_SCOPE", default="_default")
COUCHBASE_URL      = EnvVarSpec(id="COUCHBASE_URL")
COUCHBASE_USERNAME = EnvVarSpec(id="COUCHBASE_USERNAME")

#### Validation ####

def validate() -> bool:
    return env.validate(
        [
            LOG_LEVEL,
            HTTP_PORT,
            HTTP_DEBUG,
            HTTP_AUTORELOAD,
            OPPER_API_KEY,
            COUCHBASE_URL,
            COUCHBASE_BUCKET,
            COUCHBASE_USERNAME,
            COUCHBASE_PASSWORD,
            COUCHBASE_SCOPE,
        ]
    )

#### Getters ####

def get_log_level() -> str:
    return env.parse(LOG_LEVEL)

def get_http_conf() -> HttpServerConf:
    return HttpServerConf(
        host=env.parse(HTTP_HOST),
        port=env.parse(HTTP_PORT),
        debug=env.parse(HTTP_DEBUG),
        autoreload=env.parse(HTTP_AUTORELOAD),
    )

def get_couchbase_conf() -> CouchbaseConf:
    return CouchbaseConf(
        url=env.parse(COUCHBASE_URL),
        bucket=env.parse(COUCHBASE_BUCKET),
        username=env.parse(COUCHBASE_USERNAME),
        password=env.parse(COUCHBASE_PASSWORD),
    )

def get_opper_api_key() -> str:
    return env.parse(OPPER_API_KEY)
