from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from app.models.ticket_models import (
    CreateTicketRequest,
    TicketResponse,
    TicketStatus,
)
from app.models.workflow_selector_models import WorkflowSelectionRequest
from app.repositories.ticket_repository import TicketRepository
from app.repositories.workflow_transaction_repository import WorkflowTransactionRepository
from app.services.llm_workflow_selector_service import llm_workflow_selector_service
from app.services.sqs_service import SQSService
from app.services.workflow_run_service import WorkflowRunService



class TicketService:
    def __init__(self, repository: Any = None):
        self.ticket_repository = repository or TicketRepository()
        self.workflow_run_service = WorkflowRunService()
        self.workflow_transaction_repository = WorkflowTransactionRepository()
        self.sqs_service = SQSService()

    def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        now = self._current_time_iso()
        # 创建并持久化 Ticket（status = CREATED）
        ticket = TicketResponse(
            ticket_id=f"ticket_{uuid4().hex[:8]}",
            user_id=request.user_id,
            message=request.message,
            source=request.source or "unknown",
            status=TicketStatus.CREATED,
            created_at=now,
            updated_at=now,
        )

        saved_ticket = self.ticket_repository.save(ticket)
        # 调用 LLM 工作流选择服务，解析出候选工作流、提取字段及缺失字段
        selection = llm_workflow_selector_service.select_workflow(
            WorkflowSelectionRequest(
                message=saved_ticket.message,
                user_id=saved_ticket.user_id,
                source=saved_ticket.source,
            )
        )
        # 分支 A（缺少字段）：调用 mark_waiting_for_input，
        # 返回待补充状态的 Ticket；
        if not selection.is_ready_for_workflow:
            waiting_ticket = self.ticket_repository.mark_waiting_for_input(
                ticket_id=saved_ticket.ticket_id,
                selected_workflow_id=selection.selected_workflow_id,
                selected_workflow_type=selection.selected_workflow_type,
                extracted_fields=selection.extracted_fields,
                missing_fields=selection.missing_fields,
                missing_field_questions=selection.missing_field_questions,
                updated_at=self._current_time_iso(),
            )

            if waiting_ticket is None:
                raise RuntimeError("Failed to update ticket to WAITING_FOR_INPUT.")

            return waiting_ticket
        # 分支 B（字段齐全）： 
        # 构建 WorkflowRun；
        # 调用事务库 create_workflow_run_and_attach_ticket；
        # try-catch 调用 SQS 发送消息；
        # 成功则事务标记 mark_workflow_queued，失败则事务标记 mark_workflow_failed 并记录异常。   
        workflow_run = self.workflow_run_service.build_workflow_run(
            ticket_id=saved_ticket.ticket_id,
            workflow_id=selection.selected_workflow_id,
            workflow_type=selection.selected_workflow_type,
            workflow_input=selection.extracted_fields,
        )

        self.workflow_transaction_repository.create_workflow_run_and_attach_ticket(
            workflow_run=workflow_run,
            extracted_fields=selection.extracted_fields,
            updated_at=self._current_time_iso(),
        )

        try:
            self.sqs_service.send_workflow_run_message(
                workflow_run_id=workflow_run.workflow_run_id
            )

            self.workflow_transaction_repository.mark_workflow_queued(
                ticket_id=saved_ticket.ticket_id,
                workflow_run_id=workflow_run.workflow_run_id,
                updated_at=self._current_time_iso(),
            )

        except Exception as error:
            self.workflow_transaction_repository.mark_workflow_failed(
                ticket_id=saved_ticket.ticket_id,
                workflow_run_id=workflow_run.workflow_run_id,
                error_message=str(error),
                updated_at=self._current_time_iso(),
            )

            failed_ticket = self.ticket_repository.get_by_id(saved_ticket.ticket_id)

            if failed_ticket is None:
                raise

            return failed_ticket

        queued_ticket = self.ticket_repository.get_by_id(saved_ticket.ticket_id)

        if queued_ticket is None:
            raise RuntimeError("Ticket not found after workflow queueing.")

        return queued_ticket

    def get_ticket(self, ticket_id: str) -> Optional[TicketResponse]:
        return self.ticket_repository.get_by_id(ticket_id)

    def list_tickets(self) -> List[TicketResponse]:
        return self.ticket_repository.list_all()

    def update_ticket_status(
        self,
        ticket_id: str,
        status: TicketStatus,
    ) -> Optional[TicketResponse]:
        now = self._current_time_iso()
        return self.ticket_repository.update_status(
            ticket_id=ticket_id,
            status=status,
            updated_at=now,
        )

    def _current_time_iso(self) -> str:
        # 生成标准 UTC 时间戳字符串 (例如: 2026-08-13T20:13:58+00:00)
        return datetime.now(timezone.utc).isoformat()


ticket_service = TicketService()
