from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.workflow_definition_models import (
    CreateWorkflowDefinitionRequest,
    WorkflowDefinitionResponse,
)
from app.services.workflow_definition_service import workflow_definition_service


# 创建 FastAPI 路由分组对象，统一指定 URL 前缀与 Swagger API 标签分类
router = APIRouter(
    prefix="/workflow-definitions",
    tags=["Workflow Definitions"],
)


@router.post(
    "",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_definition(request: CreateWorkflowDefinitionRequest):
    """POST /workflow-definitions

    创建新的工作流定义端点。
    接收 HTTP Body 中的请求数据，调用 Service 层处理业务逻辑并返回 HTTP 201 响应。
    """
    return workflow_definition_service.create_workflow_definition(request)


@router.get(
    "",
    response_model=List[WorkflowDefinitionResponse],
)
def list_workflow_definitions():
    """GET /workflow-definitions

    获取所有工作流定义列表的 API 端点（包含 DRAFT, PUBLISHED, DISABLED 所有状态）。
    """
    return workflow_definition_service.list_workflow_definitions()


@router.get(
    "/published",
    response_model=List[WorkflowDefinitionResponse],
)
def list_published_workflow_definitions():
    """GET /workflow-definitions/published

    获取所有处于已发布 (PUBLISHED) 状态的工作流定义列表，主要用于决策分流与工单路由。
    """
    return workflow_definition_service.list_published_workflow_definitions()


@router.get(
    "/{workflow_id}",
    response_model=WorkflowDefinitionResponse,
)
def get_workflow_definition(workflow_id: str):
    """GET /workflow-definitions/{workflow_id}

    根据路径参数 workflow_id 查询特定工作流定义的 API 端点。
    如果数据不存在，抛出 HTTP 404 异常。
    """
    workflow_definition = workflow_definition_service.get_workflow_definition(
        workflow_id
    )

    # 若查无此记录，抛出 HTTP 404 Not Found 异常
    if workflow_definition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    return workflow_definition

