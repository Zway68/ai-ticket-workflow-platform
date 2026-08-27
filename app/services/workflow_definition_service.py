from datetime import datetime, timezone
from typing import Any, List, Optional

from app.models.workflow_definition_models import (
    CreateWorkflowDefinitionRequest,
    WorkflowDefinitionResponse,
)
from app.repositories.workflow_definition_repository import (
    WorkflowDefinitionRepository,
)


class WorkflowDefinitionService:
    """工作流定义服务层 (Service Layer)

    负责处理工作流定义的核心业务逻辑，如补充系统生成时间戳 (created_at/updated_at)、
    校验/转换请求模型，并将持久化操作交由 WorkflowDefinitionRepository 执行。
    """

    def __init__(self, repository: Any = None):
        """依赖注入：支持从外部传入 repository 实例（如单元测试时的 Mock 对象或不同的 DB 仓储）。
        如果不传，则默认初始化标准的 WorkflowDefinitionRepository 实例。
        """
        self.workflow_definition_repository = repository or WorkflowDefinitionRepository()

    def create_workflow_definition(
        self,
        request: CreateWorkflowDefinitionRequest,
    ) -> WorkflowDefinitionResponse:
        """创建新的工作流定义

        1. 获取当前 UTC 时间（ISO 8601 格式）。
        2. 将 API 请求模型 (CreateWorkflowDefinitionRequest) 补全系统时间字段，
           拼装成完整响应模型 (WorkflowDefinitionResponse)。
        3. 调用 Repository 层保存入库，并返回保存后的完整工作流定义。
        """
        # 获取系统当前 UTC 时间戳字符串
        now = self._current_time_iso()

        # 结合请求参数与生成的系统时间戳，构造响应模型实例
        workflow_definition = WorkflowDefinitionResponse(
            workflow_id=request.workflow_id,
            workflow_type=request.workflow_type,
            name=request.name,
            description=request.description,
            status=request.status,
            version=request.version,
            trigger_examples=request.trigger_examples,
            required_fields=request.required_fields,
            optional_fields=request.optional_fields,
            steps=request.steps,
            min_confidence_score=request.min_confidence_score,
            created_at=now,
            updated_at=now,
        )

        # 调用仓库层将工作流定义持久化存储到 DynamoDB 表中
        return self.workflow_definition_repository.save(workflow_definition)

    def get_workflow_definition(
        self,
        workflow_id: str,
    ) -> Optional[WorkflowDefinitionResponse]:
        """根据唯一标识 workflow_id 查询对应的工作流定义信息"""
        return self.workflow_definition_repository.get_by_id(workflow_id)

    def list_workflow_definitions(self) -> List[WorkflowDefinitionResponse]:
        """查询并返回系统中所有的工作流定义列表（包含所有状态）"""
        return self.workflow_definition_repository.list_all()

    def list_published_workflow_definitions(self) -> List[WorkflowDefinitionResponse]:
        """仅查询并返回已发布状态 (PUBLISHED) 的工作流定义列表"""
        return self.workflow_definition_repository.list_published()

    def _current_time_iso(self) -> str:
        """辅助方法：生成标准 ISO 8601 格式的当前 UTC 时间字符串"""
        return datetime.now(timezone.utc).isoformat()


# 导出服务单例，方便在 Router 路由层中直接 import 使用
workflow_definition_service = WorkflowDefinitionService()

