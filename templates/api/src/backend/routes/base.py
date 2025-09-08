from fastapi import APIRouter, Request, HTTPException

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

    # Check Temporal connectivity if enabled
    if conf.USE_TEMPORAL:
        try:
            temporal_client = request.app.state.temporal_client
            temporal_health = {
                "connected": temporal_client.is_connected(),
                "status": "connected" if temporal_client.is_connected() else "disconnected"
            }
            health_status["temporal"] = temporal_health

            if not temporal_client.is_connected():
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["temporal"] = {
                "status": "error",
                "message": f"Temporal error: {str(e)}"
            }
            health_status["status"] = "degraded"
    else:
        health_status["temporal"] = {
            "status": "disabled",
            "message": "Temporal is disabled (USE_TEMPORAL=False)"
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
# from .utils import CouchbaseDB
# from ..clients.couchbase_models import CouchbaseUser, create_user, get_user, list_users
#
# @router.post("/cb/users", response_model=CouchbaseUser)
# async def create_user_cb(user: CouchbaseUser, cb: CouchbaseDB):
#     """Create a user in Couchbase."""
#     user_id = await create_user(cb, user)
#     user.id = user_id
#     return user
#
# @router.get("/cb/users/{user_id}", response_model=CouchbaseUser)
# async def get_user_cb(user_id: str, cb: CouchbaseDB):
#     """Get a user from Couchbase."""
#     user = await get_user(cb, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
#
# @router.get("/cb/users", response_model=list[CouchbaseUser])
# async def list_users_cb(cb: CouchbaseDB, limit: int = 100, offset: int = 0):
#     """List users from Couchbase."""
#     return await list_users(cb, limit=limit, offset=offset)


# Temporal route examples (uncomment when using Temporal)
#
# from ..clients.temporal import start_example_workflow, get_workflow_result
#
# @router.post("/temporal/workflows/start")
# async def start_workflow(request: Request, name: str, delay_seconds: int = 2):
#     """Start an example Temporal workflow."""
#     temporal_client = request.app.state.temporal_client
#     workflow_id = await start_example_workflow(temporal_client, name, delay_seconds)
#     return {"workflow_id": workflow_id, "message": f"Started workflow for {name}"}
#
# @router.get("/temporal/workflows/{workflow_id}/result")
# async def get_workflow_result_route(request: Request, workflow_id: str):
#     """Get the result of a Temporal workflow."""
#     temporal_client = request.app.state.temporal_client
#     try:
#         result = await get_workflow_result(temporal_client, workflow_id)
#         return {"workflow_id": workflow_id, "result": result, "status": "completed"}
#     except Exception as e:
#         return {"workflow_id": workflow_id, "error": str(e), "status": "error"}
#
