from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowDefinitionStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class WorkflowFieldType(str, Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    ENUM = "ENUM"


class WorkflowFieldDefinition(BaseModel):
    name: str
    field_type: WorkflowFieldType
    description: str
    examples: List[str] = []
    required: bool = True
    allowed_values: Optional[List[str]] = None
    validation_regex: Optional[str] = None
    missing_field_question: Optional[str] = None


class CreateWorkflowDefinitionRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    workflow_type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: WorkflowDefinitionStatus = WorkflowDefinitionStatus.PUBLISHED
    version: int = 1
    trigger_examples: List[str] = []
    required_fields: List[WorkflowFieldDefinition] = []
    optional_fields: List[WorkflowFieldDefinition] = []
    steps: List[str] = []
    min_confidence_score: float = 0.85


class WorkflowDefinitionResponse(BaseModel):
    workflow_id: str
    workflow_type: str
    name: str
    description: str
    status: WorkflowDefinitionStatus
    version: int
    trigger_examples: List[str]
    required_fields: List[WorkflowFieldDefinition]
    optional_fields: List[WorkflowFieldDefinition]
    steps: List[str]
    min_confidence_score: float
    created_at: str
    updated_at: str
