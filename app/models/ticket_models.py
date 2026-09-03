from typing import Dict
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    # 已创建
    CREATED = "CREATED"
    # 已选择工作流
    WORKFLOW_SELECTED = "WORKFLOW_SELECTED"
    # 已创建工作流
    WORKFLOW_CREATED = "WORKFLOW_CREATED"
    # 已排队工作流
    WORKFLOW_QUEUED = "WORKFLOW_QUEUED"
    # 正在运行工作流
    WORKFLOW_RUNNING = "WORKFLOW_RUNNING"
    # 需要补充信息
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    # 已解决
    RESOLVED = "RESOLVED"
    # 已失败
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

    # === 当工作流成功匹配并创建执行实例时，工单需记录绑定的 workflow_run_id
    #     与提取出的参数字段，方便后续溯源与前端展示 ===
    # 已选择工作流id
    selected_workflow_id: Optional[str] = None
    # 已选择工作流类型
    selected_workflow_type: Optional[str] = None
    # 工作流运行id
    workflow_run_id: Optional[str] = None
    # 提取的字段
    extracted_fields: Dict[str, str] = {}
    # 缺失的字段
    missing_fields: List[str] = []
    #
    missing_field_questions: List[str] = []