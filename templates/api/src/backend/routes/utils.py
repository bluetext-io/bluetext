from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Annotated
from pydantic import BaseModel

from ..utils import auth, log

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
