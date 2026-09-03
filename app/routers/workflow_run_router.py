from fastapi import APIRouter, HTTPException, status

from app.models.workflow_run_models import WorkflowRunResponse
from app.services.workflow_run_service import WorkflowRunService

# 暴露标准 REST API，供前端或外部系统轮询/查询具体 Workflow 运行状态与上下文。
router = APIRouter(
    prefix="/workflow-runs",
    tags=["Workflow Runs"],
)


workflow_run_service = WorkflowRunService()


@router.get(
    "/{workflow_run_id}",
    response_model=WorkflowRunResponse,
)
def get_workflow_run(workflow_run_id: str):
    workflow_run = workflow_run_service.get_workflow_run(workflow_run_id)

    if workflow_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow run not found",
        )

    return workflow_run
