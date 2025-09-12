from fastapi import APIRouter, Request, HTTPException

from ..utils import log
from .. import conf
# from ..utils import RequestPrincipal # NOTE: uncomment to use auth
# from ..utils import DBSession # NOTE: uncomment to use postgres

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

    # Check Twilio connectivity if enabled
    if conf.USE_TWILIO:
        try:
            twilio_client = request.app.state.twilio_client
            twilio_health = {
                "connected": True,
                "status": "connected"
            }
            health_status["twilio"] = twilio_health
        except Exception as e:
            health_status["twilio"] = {
                "status": "error",
                "message": f"Twilio error: {str(e)}"
            }
            health_status["status"] = "degraded"
    else:
        health_status["twilio"] = {
            "status": "disabled",
            "message": "Twilio is disabled (USE_TWILIO=False)"
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
# import uuid
# from ..workflows.examples import GreetingWorkflow
#
# @router.post("/workflows/greeting")
# async def start_greeting_workflow(request: Request, name: str, greeting: str = "Hello"):
#     """Start a greeting workflow."""
#     temporal_client = request.app.state.temporal_client
#     workflow_id = f"greeting-{name}-{uuid.uuid4()}"
#
#     # IMPORTANT: For multiple workflow arguments, use args=[...]
#     handle = await temporal_client.start_workflow(
#         GreetingWorkflow.run,
#         args=[name, greeting],  # Multiple args must be passed as a list
#         id=workflow_id,
#         task_queue=temporal_client._config.task_queue,
#     )
#     return {"workflow_id": workflow_id, "message": f"Started workflow for {name}"}
#
# @router.get("/workflows/{workflow_id}/result")
# async def get_workflow_result(request: Request, workflow_id: str):
#     """Get the result of a workflow."""
#     temporal_client = request.app.state.temporal_client
#     try:
#         handle = temporal_client.get_workflow_handle(workflow_id)
#         result = await handle.result()
#
#         # Convert Pydantic models to dict for JSON serialization
#         if hasattr(result, 'model_dump'):
#             result = result.model_dump()
#
#         return {"workflow_id": workflow_id, "result": result, "status": "completed"}
#     except Exception as e:
#         return {"workflow_id": workflow_id, "error": str(e), "status": "error"}


# Twilio SMS route examples (uncomment when using Twilio)
#
# To enable Twilio SMS functionality:
# 1. Set USE_TWILIO = True in conf.py
# 2. Set environment variables:
#    - TWILIO_ACCOUNT_SID: Your Twilio Account SID
#    - TWILIO_AUTH_TOKEN: Your Twilio Auth Token  
#    - TWILIO_FROM_PHONE_NUMBER: Your Twilio phone number (e.g., '+15551234567')
# 3. Uncomment the routes below
#
# from pydantic import BaseModel
# from twilio.base.exceptions import TwilioRestException
#
# class SMSRequest(BaseModel):
#     to_phone_number: str
#     message: str
#
# @router.post("/sms/send")
# async def send_sms(request: Request, sms_request: SMSRequest):
#     """Send an SMS message via Twilio."""
#     if not conf.USE_TWILIO:
#         raise HTTPException(status_code=503, detail="Twilio SMS is disabled")
#     
#     try:
#         twilio_client = request.app.state.twilio_client
#         result = await twilio_client.send_sms(
#             sms_request.to_phone_number, 
#             sms_request.message
#         )
#         return {
#             "success": True,
#             "message_sid": result["sid"],
#             "status": result["status"],
#             "to": result["to"],
#             "message": "SMS sent successfully"
#         }
#     except TwilioRestException as e:
#         logger.error(f"Twilio error: {e}")
#         raise HTTPException(status_code=400, detail=f"Failed to send SMS: {e.msg}")
#     except Exception as e:
#         logger.error(f"Unexpected error sending SMS: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#
# # Example: Send SMS with Temporal workflow for delayed/scheduled messages
# @router.post("/sms/send-delayed")
# async def send_delayed_sms(request: Request, sms_request: SMSRequest, delay_minutes: int = 5):
#     """Send a delayed SMS message using Temporal workflow."""
#     if not conf.USE_TWILIO:
#         raise HTTPException(status_code=503, detail="Twilio SMS is disabled")
#     if not conf.USE_TEMPORAL:
#         raise HTTPException(status_code=503, detail="Temporal is disabled") 
#     
#     # This would require implementing a Temporal workflow for SMS
#     # Example workflow implementation would go in clients/temporal.py:
#     #
#     # @workflow.defn
#     # class DelayedSMSWorkflow:
#     #     @workflow.run
#     #     async def run(self, phone_number: str, message: str, delay_minutes: int) -> dict:
#     #         await asyncio.sleep(delay_minutes * 60)
#     #         return await workflow.execute_activity(
#     #             send_sms_activity,
#     #             args=[phone_number, message],
#     #             start_to_close_timeout=timedelta(minutes=1)
#     #         )
#     
#     temporal_client = request.app.state.temporal_client
#     workflow_id = f"delayed-sms-{uuid.uuid4()}"
#     
#     # Start workflow (implementation would depend on your Temporal setup)
#     # handle = await temporal_client.client.start_workflow(
#     #     DelayedSMSWorkflow.run,
#     #     args=[sms_request.to_phone_number, sms_request.message, delay_minutes],
#     #     id=workflow_id,
#     #     task_queue=temporal_client.config.task_queue
#     # )
#     
#     return {
#         "workflow_id": workflow_id,
#         "message": f"Delayed SMS scheduled for {delay_minutes} minutes",
#         "to": sms_request.to_phone_number
#     }
#
