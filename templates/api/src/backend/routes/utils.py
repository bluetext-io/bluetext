from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from typing import Annotated, AsyncGenerator
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils import auth, log
from .. import conf

logger = log.get_logger(__name__)

#### Auth ####

class InvalidPrincipalException(HTTPException):
    def __init__(self, detail="Invalid principal"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class PrincipalInfo(BaseModel):
    """Principal information."""
    # Add more fields here as needed - populate from claims
    claims: dict[str, str] = {}

def get_auth_client(app: FastAPI = Depends()):
    return app.state.auth_client

AuthClient = Annotated[auth.AuthClient, Depends(get_auth_client)]

http_bearer = HTTPBearer()

def get_request_principal(
    token: Annotated[str, Depends(http_bearer)], auth_client: AuthClient,
) -> PrincipalInfo:
    """Extracts principal info from the request token."""

    if auth_client:
        if not token or not token.credentials:
            raise InvalidPrincipalException()
        try:
            claims = auth_client.decode_token(token.credentials)
            return PrincipalInfo(claims=claims)
        except Exception as e:
            logger.warning(f"Failed to decode token: {e}")
            raise InvalidPrincipalException()
    else:
        return PrincipalInfo(claims={})

RequestPrincipal = Annotated[PrincipalInfo, Depends(get_request_principal)]

# NOTE: Implement variants on RequestPrincipal with constraints as needed, e.g.:
#
# def get_user_request_principal(
#     principal: Annotated[PrincipalInfo, Depends(get_request_principal)],
# ) -> PrincipalInfo:
#     if principal.claims.get("role") != "user":
#         raise InvalidPrincipalException(detail="Principal is not a user")
#     return principal
#
# UserRequestPrincipal = Annotated[PrincipalInfo, Depends(get_user_request_principal)]

#### Database ####

async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an AsyncSession for database operations.

    Usage in routes:
        from .utils import DBSession

        @router.post("/users")
        async def create_user(user: User, session: DBSession):
            return await create_user(session, user)
    """
    if not conf.USE_POSTGRES:
        raise HTTPException(status_code=503, detail="PostgreSQL is not configured")

    postgres_client = request.app.state.postgres_client
    
    async with postgres_client.get_session() as session:
        yield session


# Type alias for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db_session)]


#### Couchbase ####

def get_couchbase_client(request: Request):
    """
    FastAPI dependency that provides the Couchbase client.

    Usage in routes:
        from .utils import CouchbaseDB

        @router.post("/users")
        async def create_user(user: User, cb: CouchbaseDB):
            keyspace = cb.get_keyspace("users")
            return await cb.insert_document(keyspace, user.dict())
    """
    if not hasattr(request.app.state, 'couchbase_client'):
        raise HTTPException(status_code=503, detail="Couchbase client is not configured. Run add-couchbase-client to set up Couchbase")

    return request.app.state.couchbase_client


# Type alias for dependency injection
CouchbaseDB = Annotated['CouchbaseClient', Depends(get_couchbase_client)]
