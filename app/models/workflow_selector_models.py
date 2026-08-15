from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowSelectionRequest(BaseModel):
    message: str = Field(..., min_length=3)
    user_id: Optional[str] = None
    source: Optional[str] = "unknown"


class WorkflowSelectionResponse(BaseModel):
    selected_workflow_id: Optional[str]
    selected_workflow_type: Optional[str]
    confidence_score: float
    reason: str
    extracted_fields: Dict[str, str]
    missing_fields: List[str]
    missing_field_questions: List[str]
    is_ready_for_workflow: bool
