# app/ai/tool_models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Union, Literal, Dict
from uuid import UUID
from datetime import date, datetime, time

# --- Chore Tool Models ---
class GetChoreStatusArgs(BaseModel):
    chore_id: Optional[UUID] = Field(None, description="ID of the specific chore to check")
    user_id: Optional[UUID] = Field(None, description="ID of the user whose chores to check")

class CreateChoreArgs(BaseModel):
    title: str = Field(..., description="Title of the chore")
    description: Optional[str] = Field(None, description="Detailed description of the chore")
    assigned_to_id: UUID = Field(..., description="User ID of person assigned to the chore")
    due_date: Optional[date] = Field(None, description="When the chore is due")
    frequency: str = Field(..., description="Frequency of the chore (daily, weekly, monthly, once)")
    points: Optional[int] = Field(None, description="Points awarded for completing the chore")

class UpdateChoreStatusArgs(BaseModel):
    chore_id: UUID = Field(..., description="ID of the chore to update")
    status: str = Field(..., description="New status (pending, completed, verified, overdue)")

# --- Screen Time Tool Models ---
class GetScreenTimeUsageArgs(BaseModel):
    user_id: UUID = Field(..., description="ID of the user to check screen time for")
    start_date: Optional[date] = Field(None, description="Start date for usage period")
    end_date: Optional[date] = Field(None, description="End date for usage period")

class CheckScreenTimeAllowedArgs(BaseModel):
    user_id: UUID = Field(..., description="ID of the user to check")
    device_type: Optional[str] = Field(None, description="Type of device (mobile, tablet, computer)")

class ReportScreenTimeUsageArgs(BaseModel):
    user_id: UUID = Field(..., description="ID of the user reporting usage")
    device_id: str = Field(..., description="Identifier for the device")
    device_type: str = Field(..., description="Type of device")
    minutes_used: int = Field(..., description="Minutes of screen time used")
    date: Optional[date] = Field(None, description="Date of usage (defaults to today)")

# --- Family Tool Models ---
class GetFamilyMembersArgs(BaseModel):
    family_id: Optional[UUID] = Field(None, description="ID of the family to get members for")

# --- User Tool Models ---
class GetUserInfoArgs(BaseModel):
    user_id: Optional[UUID] = Field(None, description="ID of the user to get info for")
    username: Optional[str] = Field(None, description="Username of the user to get info for")

# --- Tool Call Models (action wrappers) ---
# Using tool_name instead of action to match service.py naming convention
class GetChoreStatusCall(BaseModel):
    tool_name: Literal["get_chore_status"] = "get_chore_status"
    arguments: GetChoreStatusArgs  # Using arguments instead of args to match service.py

class CreateChoreCall(BaseModel):
    tool_name: Literal["create_chore"] = "create_chore"
    arguments: CreateChoreArgs

class UpdateChoreStatusCall(BaseModel):
    tool_name: Literal["update_chore_status"] = "update_chore_status"
    arguments: UpdateChoreStatusArgs

# Screen Time Tool Calls
class GetScreenTimeUsageCall(BaseModel):
    tool_name: Literal["get_screen_time_usage"] = "get_screen_time_usage"
    arguments: GetScreenTimeUsageArgs

class CheckScreenTimeAllowedCall(BaseModel):
    tool_name: Literal["check_screen_time_allowed"] = "check_screen_time_allowed"
    arguments: CheckScreenTimeAllowedArgs

class ReportScreenTimeUsageCall(BaseModel):
    tool_name: Literal["report_screen_time_usage"] = "report_screen_time_usage"
    arguments: ReportScreenTimeUsageArgs

# Family Tool Calls
class GetFamilyMembersCall(BaseModel):
    tool_name: Literal["get_family_members"] = "get_family_members"
    arguments: GetFamilyMembersArgs

# User Tool Calls
class GetUserInfoCall(BaseModel):
    tool_name: Literal["get_user_info"] = "get_user_info"
    arguments: GetUserInfoArgs

# Define a model representing the case where NO tool is needed (matching service.py)
class NoToolCall(BaseModel):
    tool_name: Literal["no_tool_needed"] = "no_tool_needed"
    arguments: Optional[Dict] = Field(None, description="No arguments needed when no tool is called.")

# Combined Tool Call Union
# This tells Instructor what tools are available for the LLM to choose from
ToolCallDecision = Union[
    GetChoreStatusCall,
    CreateChoreCall,
    UpdateChoreStatusCall,
    GetScreenTimeUsageCall,
    CheckScreenTimeAllowedCall,
    ReportScreenTimeUsageCall,
    GetFamilyMembersCall,
    GetUserInfoCall,
    NoToolCall,  # Added to match service.py
]