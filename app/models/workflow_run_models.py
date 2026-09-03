from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel


class WorkflowRunStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Workflow Run 是一次 transaction 的生命周期管理对象.
# 状态机：created -> queued -> running -> completed / failed
class WorkflowRunResponse(BaseModel):
    # 每次调用工作流都会生成一个
    workflow_run_id: str
    # 工单 id
    ticket_id: str
    # 工作流 id
    workflow_id: str
    # 工作流类型
    workflow_type: str
    # 状态
    status: WorkflowRunStatus
    # 工作流输入参数
    workflow_input: Dict[str, str]
    # 创建时间
    created_at: str
    updated_at: str
    error_message: Optional[str] = None
