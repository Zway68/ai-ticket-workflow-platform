from typing import List, Optional
from uuid import uuid4
from app.models.ticket_models import (
    CreateTicketRequest,
    TicketResponse,
    TicketStatus,
)
from app.repositories.ticket_repository import ticket_repository

class TicketService:
    def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        ticket_id = f"ticket_{uuid4().hex[:8]}"
        ticket = TicketResponse(
            ticket_id=ticket_id,
            user_id=request.user_id,
            message=request.message,
            source=request.source or "unknown",
            status=TicketStatus.CREATED,
        )
        return ticket_repository.save(ticket)

    def get_ticket(self, ticket_id: str) -> Optional[TicketResponse]:
        return ticket_repository.get_by_id(ticket_id)

    def list_tickets(self) -> List[TicketResponse]:
        return ticket_repository.list_all()


ticket_service = TicketService()