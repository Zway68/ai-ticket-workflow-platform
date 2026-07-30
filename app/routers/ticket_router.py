from typing import List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status 
from app.models.ticket_models import CreateTicketRequest, TicketResponse
from app.services.ticket_service import TicketService
ticket_service = TicketService()
router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)
@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(request: CreateTicketRequest):
    response = ticket_service.create_ticket(request)
    return response
@router.get(
    "",
    response_model=List[TicketResponse],
)
def list_tickets():
    response = ticket_service.list_tickets()
    return response
@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
) 
def get_ticket(ticket_id: str):
    ticket = ticket_service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket   