from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowDefinitionStatus(str, Enum):
    """工作流定义的状态枚举"""
    DRAFT = "DRAFT"         # 草稿状态（新建但尚未生效）
    PUBLISHED = "PUBLISHED" # 已发布状态（正常在线生效）
    DISABLED = "DISABLED"   # 已下线/禁用状态


class WorkflowFieldType(str, Enum):
    """工作流中槽位/属性定义的数据类型枚举"""
    STRING = "STRING"   # 字符串
    NUMBER = "NUMBER"   # 数值类型
    BOOLEAN = "BOOLEAN" # 布尔类型
    ENUM = "ENUM"       # 枚举值（多选一）


class WorkflowFieldDefinition(BaseModel):
    """工作流字段/槽位定义模型

    定义完成该工作流需要提取或收集的具体字段约束与规则。
    """
    name: str                                           # 字段名称 (例如 "refund_amount")
    field_type: WorkflowFieldType                       # 字段数据类型
    description: str                                    # 字段用途描述
    examples: List[str] = []                            # 该字段的示例取值列表
    required: bool = True                               # 是否为必填字段
    allowed_values: Optional[List[str]] = None          # 如果是 ENUM 类型，可允许的取值列表
    validation_regex: Optional[str] = None              # 字段值的正则表达式校验规则
    missing_field_question: Optional[str] = None        # 当缺少该必填字段时，AI 提示向用户追问的话术


class CreateWorkflowDefinitionRequest(BaseModel):
    """创建工作流定义的 API 输入请求模型 (Request Body)"""
    workflow_id: str = Field(..., min_length=1)         # 工作流唯一标识符 (例如 "wf_refund_v1")
    workflow_type: str = Field(..., min_length=1)       # 工作流分类类型 (例如 "BILLING")
    name: str = Field(..., min_length=1)                # 工作流展示名称
    description: str = Field(..., min_length=1)         # 工作流功能描述
    status: WorkflowDefinitionStatus = WorkflowDefinitionStatus.PUBLISHED # 初始化状态，默认 PUBLISHED
    version: int = 1                                    # 版本号，默认 1
    trigger_examples: List[str] = []                    # 触发该工作流的用户自然语言提示词示例（用于 LLM / Selector 匹配）
    required_fields: List[WorkflowFieldDefinition] = [] # 执行该工作流所需的必填字段列表
    optional_fields: List[WorkflowFieldDefinition] = [] # 可选字段列表
    steps: List[str] = []                               # 工作流执行的步骤节点列表
    min_confidence_score: float = 0.85                  # 触发该工作流的最少置信度门槛分数


class WorkflowDefinitionResponse(BaseModel):
    """工作流定义的 API 输出响应与数据库持久化模型 (Response Body & DB Entity)"""
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
    created_at: str                                     # 系统生成的创建时间 (ISO 8601)
    updated_at: str                                     # 系统生成的最后修改时间 (ISO 8601)

