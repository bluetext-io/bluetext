from pydantic import BaseModel

from ..utils import auth, env, log
from ..utils.env import EnvVarSpec

from couchbase_client import CouchbaseConf

#### Env Vars ####

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

VALIDATED_ENV_VARS = [
    COUCHBASE_HOST,
    COUCHBASE_USERNAME,
    COUCHBASE_PASSWORD,
    COUCHBASE_BUCKET,
    COUCHBASE_PROTOCOL
]


#### Getters ####

def get_couchbase_conf():
    """Get Couchbase connection configuration."""
    return CouchbaseConf(
        host=env.parse(COUCHBASE_HOST),
        username=env.parse(COUCHBASE_USERNAME),
        password=env.parse(COUCHBASE_PASSWORD),
        bucket=env.parse(COUCHBASE_BUCKET),
        protocol=env.parse(COUCHBASE_PROTOCOL),
    )
