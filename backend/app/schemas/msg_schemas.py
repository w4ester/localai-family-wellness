# ./backend/app/schemas/msg_schemas.py
"""
Pydantic schemas for simple message responses (e.g., status or detail messages).
"""
from pydantic import BaseModel, Field

class Msg(BaseModel):
    """
    Generic message response schema.
    """
    msg: str = Field(..., description="A message detailing the response status.")

# You could also define more specific status messages if needed
# class ActionStatus(BaseModel):
#     success: bool
#     detail: Optional[str] = None