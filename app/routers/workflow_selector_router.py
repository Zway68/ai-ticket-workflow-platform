"""
工作流选择器路由模块。

提供外部调用入口，通过接收用户输入的消息，分析并选择合适的工作流。
"""

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
    """POST /workflow-selector/select

    根据用户发送的自然语言消息，智能匹配并分流至最合适的工作流的 API 端点。
    同时提取相关槽位（字段）信息，并检查是否有缺失的必填字段。
    """
    return llm_workflow_selector_service.select_workflow(request)

