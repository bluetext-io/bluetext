from pydantic import BaseModel, Field
from typing import Any

class ScheduleChange(BaseModel):
    employee_name: str = Field(description="The name of the employee originally scheduled for the date")
    target_date: str = Field(description="The date of the requested change in YYYY-MM-DD format")
    suggested_replacement: str = Field(description="The suggested replacement employee, if any")

# Schedule Change Request Analysis
class ScheduleChangeAnalysis(BaseModel):
    thoughts: str = Field(description="The AI's thought process while analyzing the request")
    original_query: str = Field(description="The original query text that was analyzed")
    changes: list[ScheduleChange] = Field(description="The suggested changes to the schedule")
    reason: str | None = Field(description="The extracted reason for the change")
    recommendation: str = Field(
        description="Whether the change should be approved, denied, or needs discussion",
        enum=["approve", "deny", "discuss"]
    )
    reasoning: str = Field(description="Detailed explanation for the recommendation")


# Employee Model
class Employee(BaseModel):
    name: str
    employee_number: str
    first_line_support_count: int = 0
    known_absences: list[str] = Field(default_factory=list)  # ISO format dates
    metadata: dict[str, Any] = Field(default_factory=dict)


# Schedule Model
class Schedule(BaseModel):
    date: str  # ISO format date
    first_line_support: str  # Employee number


# Rules Model
class Rules(BaseModel):
    max_days_per_week: int = 3  # Maximum consecutive days as first line support
    preferred_balance: float = 0.2  # Preferred maximum difference from average (20%)


# API Request/Response Models
class MessageResponse(BaseModel):
    message: str


class ScheduleChangeRequest(BaseModel):
    request_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleChangeResponse(BaseModel):
    request: str
    analysis: ScheduleChangeAnalysis


class EmployeeCreateRequest(BaseModel):
    name: str
    employee_number: str
    known_absences: list[str] = Field(default_factory=list)  # ISO format dates
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleCreateRequest(BaseModel):
    date: str  # ISO format date
    first_line_support: str  # Employee number


class RulesUpdateRequest(BaseModel):
    max_days_per_week: int | None = None
    preferred_balance: float | None = None
