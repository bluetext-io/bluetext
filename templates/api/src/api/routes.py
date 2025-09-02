from fastapi import APIRouter, Path, Depends, HTTPException, Request
from typing import Annotated, List, Dict, Optional

from opperai import Opper, trace
from .clients.scheduling import SchedulingClient
from .utils import log
from .models import (
    Employee, Schedule, Rules,
    ScheduleChangeRequest, ScheduleChangeResponse, ScheduleChangeAnalysis,
    MessageResponse, EmployeeCreateRequest, ScheduleCreateRequest, RulesUpdateRequest
)

logger = log.get_logger(__name__)

router = APIRouter()

def get_db_handle(request: Request) -> SchedulingClient:
    """Util for getting the Couchbase client from the request state."""
    return request.app.state.db

def get_opper_handle(request: Request) -> Opper:
    """Util for getting the Opper client from the request state."""
    return request.app.state.opper

DbHandle = Annotated[SchedulingClient, Depends(get_db_handle)]
OpperHandle = Annotated[Opper, Depends(get_opper_handle)]

#### Helper Functions ####

@trace
def process_schedule_change(
    opper: Opper,
    request_text: str,
    employees: List[Dict],
    current_schedule: List[Dict],
    rules: Dict
) -> ScheduleChangeAnalysis:
    """Process a natural language schedule change request."""
    analysis_result, _ = opper.call(
        name="analyze_schedule_change",
        instructions="""
        Analyze this schedule change request considering the rules and provide a clear recommendation.
        Extract the employee name, target dates, reason for change, and suggest replacements if applicable.
        Use the provided employee and schedule information to make an informed recommendation.
        Consider workload balance, consecutive shifts, and employee absences in your analysis.
        Include the original query text in your analysis.
        """,
        input={
            "request": request_text,
            "employees": employees,
            "current_schedule": current_schedule,
            "rules": rules
        },
        output_type=ScheduleChangeAnalysis
    )

    # Make sure the original query is included in the analysis
    analysis_result.original_query = request_text
    logger.info(f"Schedule change request analysis: {analysis_result.dict()}")
    return analysis_result

#### Routes ####

@router.get("", response_model=MessageResponse)
async def hello() -> MessageResponse:
    return MessageResponse(message="Hello from the Employee Scheduling API!")

# Employee Routes
@router.post("/employees", response_model=Employee)
async def create_employee(
    db: DbHandle,
    request: EmployeeCreateRequest
) -> Employee:
    """Create a new employee."""
    employee_id = db.create_employee(
        name=request.name,
        employee_number=request.employee_number,
        known_absences=request.known_absences,
        metadata=request.metadata
    )
    employee = db.get_employee(employee_id)
    return Employee(**employee)

@router.get("/employees", response_model=List[Employee])
async def get_employees(
    db: DbHandle
) -> List[Employee]:
    """Get all employees."""
    employees = db.get_employees()
    return [Employee(**emp) for emp in employees]

@router.get("/employees/{employee_number}", response_model=Employee)
async def get_employee(
    db: DbHandle,
    employee_number: str = Path(..., description="The employee number")
) -> Employee:
    """Get an employee by employee number."""
    employee = db.get_employee(employee_number)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee with number {employee_number} not found")
    return Employee(**employee)

@router.put("/employees/{employee_number}", response_model=Employee)
async def update_employee(
    db: DbHandle,
    request: EmployeeCreateRequest,
    employee_number: str = Path(..., description="The employee number")
) -> Employee:
    """Update an employee."""
    # Check if employee exists
    if not db.get_employee(employee_number):
        raise HTTPException(status_code=404, detail=f"Employee with number {employee_number} not found")

    updates = request.dict(exclude_unset=True)
    success = db.update_employee(employee_number, updates)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update employee")

    employee = db.get_employee(employee_number)
    return Employee(**employee)

@router.delete("/employees/{employee_number}", response_model=MessageResponse)
async def delete_employee(
    db: DbHandle,
    employee_number: str = Path(..., description="The employee number")
) -> MessageResponse:
    """Delete an employee."""
    # Check if employee exists
    if not db.get_employee(employee_number):
        raise HTTPException(status_code=404, detail=f"Employee with number {employee_number} not found")

    success = db.delete_employee(employee_number)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete employee")

    return MessageResponse(message=f"Employee {employee_number} deleted successfully")

# Schedule Routes
@router.post("/schedules", response_model=Schedule)
async def create_schedule(
    db: DbHandle,
    request: ScheduleCreateRequest
) -> Schedule:
    """Create a new schedule entry."""
    # Check if employee exists
    if not db.get_employee(request.first_line_support):
        raise HTTPException(status_code=404, detail=f"Employee with number {request.first_line_support} not found")

    date_str = db.create_schedule(
        date_str=request.date,
        employee_number=request.first_line_support
    )

    schedule = db.get_schedule(date_str)
    return Schedule(**schedule)

@router.get("/schedules", response_model=List[Schedule])
async def get_schedules(
    db: DbHandle,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Schedule]:
    """Get schedules within a date range."""
    schedules = db.get_schedules(start_date, end_date)
    return [Schedule(**schedule) for schedule in schedules]

@router.get("/schedules/{date}", response_model=Schedule)
async def get_schedule(
    db: DbHandle,
    date: str = Path(..., description="The date in ISO format (YYYY-MM-DD)")
) -> Schedule:
    """Get a schedule by date."""
    schedule = db.get_schedule(date)
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule for date {date} not found")
    return Schedule(**schedule)

@router.put("/schedules/{date}", response_model=Schedule)
async def update_schedule(
    db: DbHandle,
    request: ScheduleCreateRequest,
    date: str = Path(..., description="The date in ISO format (YYYY-MM-DD)")
) -> Schedule:
    """Update a schedule entry."""
    # Check if schedule exists
    if not db.get_schedule(date):
        raise HTTPException(status_code=404, detail=f"Schedule for date {date} not found")

    # Check if employee exists
    if not db.get_employee(request.first_line_support):
        raise HTTPException(status_code=404, detail=f"Employee with number {request.first_line_support} not found")

    success = db.update_schedule(date, request.first_line_support)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update schedule")

    schedule = db.get_schedule(date)
    return Schedule(**schedule)

@router.delete("/schedules/{date}", response_model=MessageResponse)
async def delete_schedule(
    db: DbHandle,
    date: str = Path(..., description="The date in ISO format (YYYY-MM-DD)")
) -> MessageResponse:
    """Delete a schedule entry."""
    # Check if schedule exists
    if not db.get_schedule(date):
        raise HTTPException(status_code=404, detail=f"Schedule for date {date} not found")

    success = db.delete_schedule(date)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete schedule")

    return MessageResponse(message=f"Schedule for date {date} deleted successfully")

# Rules Routes
@router.get("/rules", response_model=Rules)
async def get_rules(
    db: DbHandle
) -> Rules:
    """Get the scheduling system rules."""
    rules = db.get_rules()
    return Rules(**rules)

@router.put("/rules", response_model=Rules)
async def update_rules(
    db: DbHandle,
    request: RulesUpdateRequest
) -> Rules:
    """Update the scheduling system rules."""
    updates = {k: v for k, v in request.dict().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid updates provided")

    success = db.update_rules(updates)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update rules")

    rules = db.get_rules()
    return Rules(**rules)

# Schedule Change Request
@router.post("/schedule-changes", response_model=ScheduleChangeResponse)
async def process_schedule_change_request(
    request: ScheduleChangeRequest,
    db: DbHandle,
    opper: OpperHandle
) -> ScheduleChangeResponse:
    """Process a natural language schedule change request."""
    # Get all employees
    try:
        employees = db.get_employees()
        formatted_employees = [
            {
                "name": emp["name"],
                "employee_number": emp["employee_number"],
                "first_line_support_count": emp["first_line_support_count"],
                "known_absences": emp["known_absences"]
            }
            for emp in employees
        ]
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

    # Get all schedules
    try:
        schedules = db.get_schedules()
        formatted_schedules = [
            {
                "date": schedule["date"],
                "first_line_support": schedule["first_line_support"]
            }
            for schedule in schedules
        ]
    except Exception as e:
        logger.error(f"Error fetching schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")

    # Get rules
    try:
        rules = db.get_rules()
    except Exception as e:
        logger.error(f"Error fetching rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

    # Process the request
    try:
        analysis = process_schedule_change(
            opper,
            request.request_text,
            formatted_employees,
            formatted_schedules,
            rules
        )
        logger.info("Completed schedule change analysis")
    except Exception as e:
        logger.error(f"Error in schedule change analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing schedule change: {str(e)}")

    # Apply changes to the schedule if recommended
    try:
        if (analysis.recommendation == "approve"):
            for change in analysis.changes:
                target_date = change.target_date
                suggested_replacement = change.suggested_replacement

                # Find the employee number for the suggested replacement
                replacement_employee = next(
                    (emp for emp in employees if emp["name"] == suggested_replacement),
                    None
                )

                if replacement_employee:
                    # Check if the schedule exists for that date
                    existing_schedule = db.get_schedule(target_date)

                    if existing_schedule:
                        # Update the existing schedule
                        success = db.update_schedule(
                            target_date,
                            replacement_employee["employee_number"]
                        )
                        logger.info(
                            f"Schedule change applied: Date {target_date}, "
                            f"New employee: {suggested_replacement}, "
                            f"Success: {success}"
                        )
                    else:
                        # Create a new schedule if it doesn't exist
                        db.create_schedule(
                            target_date,
                            replacement_employee["employee_number"]
                        )
                        logger.info(
                            f"New schedule created: Date {target_date}, "
                            f"Employee: {suggested_replacement}"
                        )
    except Exception as e:
        logger.error(f"Error applying schedule changes: {str(e)}")

    return ScheduleChangeResponse(
        request=request.request_text,
        analysis=analysis
    )
