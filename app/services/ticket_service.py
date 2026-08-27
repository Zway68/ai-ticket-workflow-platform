from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from app.models.ticket_models import (
    CreateTicketRequest,
    TicketResponse,
    TicketStatus,
)
from app.repositories.ticket_repository import TicketRepository


class TicketService:
    def __init__(self, repository: Any = None):
        self.ticket_repository = repository or TicketRepository()

    def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        now = self._current_time_iso()
        ticket_id = f"ticket_{uuid4().hex[:8]}"

        ticket = TicketResponse(
            ticket_id=ticket_id,
            user_id=request.user_id,
            message=request.message,
            source=request.source or "unknown",
            status=TicketStatus.CREATED,
            created_at=now,
            updated_at=now,
        )
        return self.ticket_repository.save(ticket)

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
