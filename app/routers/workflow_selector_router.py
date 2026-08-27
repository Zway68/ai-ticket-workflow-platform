from fastapi import APIRouter

from app.models.workflow_selector_models import (
    WorkflowSelectionRequest,
    WorkflowSelectionResponse,
)
from app.services.llm_workflow_selector_service import (
    llm_workflow_selector_service,
)


router = APIRouter(
    prefix="/workflow-selector",
    tags=["Workflow Selector"],
)


@router.post(
    "/select",
    response_model=WorkflowSelectionResponse,
)
def select_workflow(request: WorkflowSelectionRequest):
    return llm_workflow_selector_service.select_workflow(request)
