from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from opperai import Opper
from datetime import datetime, timedelta
import asyncio

from .clients.scheduling import SchedulingClient
from .routes import router
from .utils import log
from . import conf

log.init(conf.get_log_level())
logger = log.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    cb_conf = conf.get_couchbase_conf()
    app.state.db = SchedulingClient(
        url=cb_conf.url,
        username=cb_conf.username,
        password=cb_conf.password,
        bucket_name=cb_conf.bucket,
        scope=cb_conf.scope
    )
    try:
        app.state.db.connect()
        logger.info("Connected to Couchbase database")

    except Exception:
        logger.warning("Couldn't connect to Couchbase - retrying on next request.")

    # Run init_default_data as an async task
    asyncio.create_task(init_default_data_async(app.state.db))
    app.state.opper = Opper(api_key=conf.get_opper_api_key())

    logger.info("Application initialized")

    yield

def init_default_data(db: SchedulingClient):
    """Initialize default employees and schedules for demo purposes."""
    # Check if we already have employees
    employees = db.get_employees()

    # Define a fixed reference date for absences (January 1, 2024)
    reference_date = datetime(2024, 1, 1).date()
    today = datetime.now().date()

    # Configure absence patterns (every Nth day from the reference date)
    absence_patterns = {
        "EMP001": 3,  # Every 3rd day from reference date
        "EMP002": 5,  # Every 5th day from reference date
        "EMP004": 7   # Every 7th day from reference date
    }

    # Create/update employees
    default_employees = [
        {"name": "Lars Larsson", "employee_number": "EMP001", "known_absences": []},
        {"name": "Dagobert Dagobertsson", "employee_number": "EMP002", "known_absences": []},
        {"name": "Karl-Gustav Karlgustavsson", "employee_number": "EMP003", "known_absences": []},
        {"name": "Kerstin Kerstinsdotter", "employee_number": "EMP004", "known_absences": []},
        {"name": "Maj-Britt Majbrittdotter", "employee_number": "EMP005", "known_absences": []}
    ]

    # Generate known absences for the next 30 days
    for emp in default_employees:
        employee_id = emp["employee_number"]
        if employee_id in absence_patterns:
            pattern_days = absence_patterns[employee_id]
            absences = []

            for i in range(30):  # Look ahead 30 days
                check_date = today + timedelta(days=i)
                days_since_reference = (check_date - reference_date).days

                if days_since_reference % pattern_days == 0:
                    absences.append(check_date.strftime("%Y-%m-%d"))

            emp["known_absences"] = absences

    if not employees:
        logger.info("Initializing default employees...")

        for emp in default_employees:
            try:
                db.create_employee(
                    name=emp["name"],
                    employee_number=emp["employee_number"],
                    known_absences=emp["known_absences"]
                )
                logger.info(f"Created default employee: {emp['name']}")
            except Exception as e:
                logger.warning(f"Failed to create employee {emp['name']}: {str(e)}")
    else:
        logger.info(f"Found {len(employees)} existing employees, updating absences...")

        # Update existing employees with new absence patterns
        for emp in default_employees:
            try:
                existing_employee = db.get_employee(emp["employee_number"])
                if existing_employee:
                    db.update_employee(emp["employee_number"], {"known_absences": emp["known_absences"]})
                    logger.info(f"Updated absences for employee: {emp['name']}")
            except Exception as e:
                logger.warning(f"Failed to update employee {emp['name']}: {str(e)}")

    # Always front-fill the next 7 days of schedules
    logger.info("Front-filling schedules for the next 7 days...")

    for i in range(7):
        day = today + timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")

        # Check if schedule already exists for this date
        existing_schedule = db.get_schedule(date_str)

        if existing_schedule:
            logger.info(f"Schedule for {date_str} already exists, skipping")
            continue

        # Assign an employee who's not absent on this day
        available_employees = [e for e in default_employees if date_str not in e["known_absences"]]

        if available_employees:
            # Select employee based on index to distribute evenly
            emp_number = available_employees[i % len(available_employees)]["employee_number"]
        else:
            # If all employees are absent, just use round-robin
            emp_number = default_employees[i % len(default_employees)]["employee_number"]

        try:
            db.create_schedule(date_str=date_str, employee_number=emp_number)
            logger.info(f"Created schedule for {date_str}")
        except Exception as e:
            logger.warning(f"Failed to create schedule for {date_str}: {str(e)}")


async def init_default_data_async(db: SchedulingClient):
    """Async version of init_default_data that runs as a background task."""
    logger.info("Starting async initialization of default data...")
    try:
        # Run the original function in a separate thread to avoid blocking
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: init_default_data(db))
        logger.info("Async initialization of default data completed")
    except Exception as e:
        logger.error(f"Error in async initialization of default data: {str(e)}")

app = FastAPI(
    title="Employee Scheduling API",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)
app.include_router(router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main():
    if not conf.validate():
        raise ValueError("Invalid configuration.")

    http_conf = conf.get_http_conf()
    logger.info(f"Starting API on port {http_conf.port}")
    uvicorn.run(
        "api.main:app",
        host=http_conf.host,
        port=http_conf.port,
        reload=http_conf.autoreload,
        log_level="debug" if http_conf.debug else "info",
        log_config=None
    )
