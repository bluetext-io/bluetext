from fastapi import APIRouter, Request

from ..utils import log
from .. import conf
# from ..utils import RequestPrincipal # NOTE: uncomment to use auth

logger = log.get_logger(__name__)
router = APIRouter()

#### Routes ####

@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "backend",
    }

    # Check database connectivity if enabled
    if conf.USE_POSTGRES:
        postgres_client = request.app.state.postgres_client
        db_health = postgres_client.health_check()
        health_status["database"] = db_health

        if not db_health.get("connected", False):
            health_status["status"] = "degraded"
    else:
        health_status["database"] = {
            "status": "disabled",
            "message": "PostgreSQL is disabled (USE_POSTGRES=False)"
        }

    # Check Couchbase connectivity if enabled
    if conf.USE_COUCHBASE:
        try:
            couchbase_client = request.app.state.couchbase_client
            couchbase_health = couchbase_client.health_check()
            health_status["couchbase"] = couchbase_health

            if not couchbase_health.get("connected", False):
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["couchbase"] = {
                "status": "error",
                "message": f"Couchbase error: {str(e)}"
            }
            health_status["status"] = "degraded"
    else:
        health_status["couchbase"] = {
            "status": "disabled",
            "message": "Couchbase is disabled (USE_COUCHBASE=False)"
        }

    return health_status

# PostgreSQL route example using SQLModel (uncomment when using PostgreSQL)
#
# from .utils import DBSession
# from ..db.models import User, create_user, get_user, get_users
#
# @router.post("/users", response_model=User)
# async def create_user_route(user: User, session: DBSession):
#     """Create a new user."""
#     return await create_user(session, user)
#
# @router.get("/users/{user_id}", response_model=User)
# async def get_user_route(user_id: int, session: DBSession):
#     """Get a user by ID."""
#     user = await get_user(session, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
#
# @router.get("/users", response_model=list[User])
# async def list_users_route(session: DBSession, skip: int = 0, limit: int = 100):
#     """List all users with pagination."""
#     return await get_users(session, skip=skip, limit=limit)


# Couchbase route example (uncomment when using Couchbase)
#
# @router.post("/couchbase/users")
# async def create_user_couchbase(request: Request, name: str, email: str):
#     """Create a user in Couchbase."""
#     couchbase_client = request.app.state.couchbase_client
#     keyspace = couchbase_client.get_keyspace("users")
#     user_data = {"name": name, "email": email}
#     user_id = await couchbase_client.insert_document(keyspace, user_data)
#     return {"id": user_id}
#
