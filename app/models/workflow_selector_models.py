"""工作流选择器数据模型"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowSelectionRequest(BaseModel):
    """工作流自动选择请求"""
    message: str = Field(..., min_length=3)  # 用户输入的自然语言消息
    user_id: Optional[str] = None            # 用户 ID（可选）
    source: Optional[str] = "unknown"        # 消息来源（如 chat, email, slack）


class WorkflowSelectionResponse(BaseModel):
    """工作流自动选择响应"""
    selected_workflow_id: Optional[str]       # 匹配到的工作流 ID，未匹配到时为 null
    selected_workflow_type: Optional[str]     # 工作流类型，未匹配到时为 null
    confidence_score: float                   # 匹配置信度 (0.0 ~ 1.0)
    reason: str                               # 匹配或未匹配的原因
    extracted_fields: Dict[str, str]          # 提取出的字段键值对 ({field_name: field_value})
    missing_fields: List[str]                 # 缺失的必填字段列表
    missing_field_questions: List[str]        # 针对缺失必填字段的提问列表
    is_ready_for_workflow: bool               # 是否已满足执行条件（置信度达标且无缺失必填项）


