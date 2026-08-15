from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    CREATED = "CREATED"
    WORKFLOW_SELECTED = "WORKFLOW_SELECTED"
    WORKFLOW_CREATED = "WORKFLOW_CREATED"
    WORKFLOW_QUEUED = "WORKFLOW_QUEUED"
    WORKFLOW_RUNNING = "WORKFLOW_RUNNING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class CreateTicketRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=5)
    source: Optional[str] = "unknown"


class UpdateTicketStatusRequest(BaseModel):
    status: TicketStatus


class TicketResponse(BaseModel):
    ticket_id: str
    user_id: str
    message: str
    source: str
    status: TicketStatus
    created_at: str
    updated_at: str