from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.ticket_models import (
    CreateTicketRequest,
    TicketResponse,
    UpdateTicketStatusRequest,
)
from app.services.ticket_service import ticket_service

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
    return ticket_service.create_ticket(request)


@router.get(
    "",
    response_model=List[TicketResponse],
)
def list_tickets():
    return ticket_service.list_tickets()


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


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
)
def update_ticket_status(
    ticket_id: str,
    request: UpdateTicketStatusRequest,
):
    ticket = ticket_service.update_ticket_status(
        ticket_id=ticket_id,
        status=request.status,
    )
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket
