# ./backend/app/schemas/screen_time_schemas.py
"""
Pydantic schemas for Screen Time rules, usage, and requests.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, time

# Import enums from the model file
from app.db.models.screen_time_model import DayOfWeek, AppCategory, RequestStatus

# Import related schemas
from .user_schemas import UserReadMinimal # For assignee, creator, verifier


# --- ScreenTimeRule Schemas ---

class ScreenTimeRuleBase(BaseModel):
    name: Optional[str] = Field(None, description="Name for the screen time rule", examples=["Weekday School Night Limit"])
    description: Optional[str] = Field(None, description="Optional description of the rule")
    user_id: Optional[UUID] = Field(None, description="The ID of the child this rule applies to") # Required on Create
    daily_limit_minutes: Optional[int] = Field(None, description="Total daily screen time limit in minutes", ge=0)
    active_days: Optional[List[DayOfWeek]] = Field(None, description="Days of the week when this rule is active", examples=[["monday", "tuesday"]])
    start_time: Optional[time] = Field(None, description="Time when screen time allowance starts (HH:MM)")
    end_time: Optional[time] = Field(None, description="Time when screen time allowance ends (HH:MM)")
    blocked_apps: Optional[List[str]] = Field(None, description="List of blocked app identifiers (bundle IDs, package names)")
    allowed_apps: Optional[List[str]] = Field(None, description="List of allowed app identifiers (overrides blocks)")
    blocked_categories: Optional[List[AppCategory]] = Field(None, description="List of blocked app categories")
    allowed_categories: Optional[List[AppCategory]] = Field(None, description="List of allowed app categories (overrides blocks)")
    is_active: Optional[bool] = Field(True, description="Whether the rule is currently enabled")
    can_request_extension: Optional[bool] = Field(True, description="Can the user request more time under this rule?")
    extension_limit_minutes: Optional[int] = Field(None, description="Maximum extra minutes grantable per request", ge=0)


class ScreenTimeRuleCreate(ScreenTimeRuleBase):
    name: str = Field(..., examples=["Weekday Limit"])
    user_id: UUID # Child user ID is required when creating a rule
    family_id: UUID # Must be provided or inferred from creator context


class ScreenTimeRuleUpdate(ScreenTimeRuleBase):
    # All fields are optional during update
    # Set fields to None to clear them (e.g., remove daily limit)
    pass


class ScreenTimeRuleRead(ScreenTimeRuleBase):
    id: UUID
    name: str
    family_id: UUID
    user_id: UUID
    is_active: bool
    can_request_extension: bool
    created_at: datetime
    updated_at: datetime
    # Optionally include the user object if needed
    # user: Optional[UserReadMinimal] = None

    class Config:
        from_attributes = True


# --- ScreenTimeUsage Schemas ---

class ScreenTimeUsageBase(BaseModel):
    user_id: Optional[UUID] = Field(None, description="User whose usage this is") # Required on Create
    start_time: Optional[datetime] = Field(None, description="Timestamp when the usage session started") # Required on Create
    end_time: Optional[datetime] = Field(None, description="Timestamp when the usage session ended") # Required on Create
    duration_seconds: Optional[int] = Field(None, description="Duration of the session in seconds", ge=0) # Required on Create
    device_id: Optional[str] = Field(None, description="Identifier of the device")
    device_name: Optional[str] = Field(None, description="Name of the device")
    app_identifier: Optional[str] = Field(None, description="Identifier of the app used")
    app_name: Optional[str] = Field(None, description="Name of the app used")
    app_category: Optional[str] = Field(None, description="Category of the app used") # Or use AppCategory enum
    activity_type: Optional[str] = Field(None, description="Type of activity detected")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ScreenTimeUsageCreate(ScreenTimeUsageBase):
    # Fields required when an agent logs usage
    user_id: UUID
    start_time: datetime
    end_time: datetime
    duration_seconds: int = Field(..., ge=0)

    @model_validator(mode='after')
    def check_times_and_duration(self) -> 'ScreenTimeUsageCreate':
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValueError('end_time must be after start_time')
            # Optional: Validate duration against start/end time difference
            # calculated_duration = (self.end_time - self.start_time).total_seconds()
            # if abs(calculated_duration - self.duration_seconds) > 5: # Allow small discrepancies
            #     raise ValueError('duration_seconds does not match start_time and end_time')
        return self


class ScreenTimeUsageRead(ScreenTimeUsageBase):
    id: UUID
    user_id: UUID
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- ScreenTimeExtensionRequest Schemas ---

class ScreenTimeExtensionRequestBase(BaseModel):
    user_id: Optional[UUID] = Field(None, description="ID of the user making the request") # Required on Create
    rule_id: Optional[UUID] = Field(None, description="ID of the rule the request applies to") # Required on Create
    requested_minutes: Optional[int] = Field(None, description="Number of extra minutes requested", gt=0) # Required on Create
    reason: Optional[str] = Field(None, description="Reason provided by the user for the request")
    status: Optional[RequestStatus] = Field(RequestStatus.PENDING, description="Current status of the request")


class ScreenTimeExtensionRequestCreate(ScreenTimeExtensionRequestBase):
    user_id: UUID
    rule_id: UUID
    requested_minutes: int = Field(..., gt=0)


class ScreenTimeExtensionRequestUpdate(BaseModel): # Response from Parent/Admin
    status: RequestStatus = Field(..., description="New status (approved or denied)")
    approved_minutes: Optional[int] = Field(None, description="Minutes granted (if approved, <= rule limit)", ge=0)
    response_note: Optional[str] = Field(None, description="Optional note from the responder")

    @model_validator(mode='after')
    def check_approved_minutes(self) -> 'ScreenTimeExtensionRequestUpdate':
        if self.status == RequestStatus.APPROVED and self.approved_minutes is None:
            raise ValueError("approved_minutes must be provided if status is 'approved'")
        if self.status == RequestStatus.DENIED:
            self.approved_minutes = None # Ensure minutes are null if denied
        return self


class ScreenTimeExtensionRequestRead(ScreenTimeExtensionRequestBase):
    id: UUID
    user_id: UUID
    rule_id: UUID
    requested_minutes: int
    status: RequestStatus # Required when reading
    created_at: datetime
    updated_at: datetime

    # Response fields
    responded_at: Optional[datetime] = None
    responded_by_id: Optional[UUID] = None
    approved_minutes: Optional[int] = None
    response_note: Optional[str] = None

    # Optional related objects
    # user: Optional[UserReadMinimal] = None
    # rule: Optional[ScreenTimeRuleRead] = None # Might cause deep nesting
    # responded_by: Optional[UserReadMinimal] = None

    class Config:
        from_attributes = True