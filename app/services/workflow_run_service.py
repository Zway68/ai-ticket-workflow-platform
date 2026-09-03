from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from app.models.workflow_run_models import WorkflowRunResponse, WorkflowRunStatus
from app.repositories.workflow_run_repository import WorkflowRunRepository

# 负责 WorkflowRun 业务对象的构建、ID 派生与校验，隔离上层业务与底层存储（DynamoDB），
# 屏蔽底层储存需要实现“原子性”操作。
# 保护数据库（Security & Validation）校验数据、并发控制

class WorkflowRunService:
    def __init__(self):
        self.workflow_run_repository = WorkflowRunRepository()

    def build_workflow_run(
        self,
        ticket_id: str,
        workflow_id: str,
        workflow_type: str,
        workflow_input: Dict[str, str],
    ) -> WorkflowRunResponse:
        now = self._current_time_iso()

        return WorkflowRunResponse(
            workflow_run_id=f"run_{uuid4().hex[:8]}",
            ticket_id=ticket_id,
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            status=WorkflowRunStatus.CREATED,
            workflow_input=workflow_input,
            created_at=now,
            updated_at=now,
        )

    def get_workflow_run(
        self,
        workflow_run_id: str,
    ) -> Optional[WorkflowRunResponse]:
        return self.workflow_run_repository.get_by_id(workflow_run_id)

    def _current_time_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
