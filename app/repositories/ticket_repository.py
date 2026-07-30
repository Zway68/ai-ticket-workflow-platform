from typing import Dict, List, Optional
from app.models.ticket_models import TicketResponse
class TicketRepository:
    def __init__(self):
        self.tickets: Dict[str, TicketResponse] = {}
    def save(self, ticket: TicketResponse) -> TicketResponse:
        self.tickets[ticket.ticket_id] = ticket
        return ticket
    def get_by_id(self, ticket_id: str) -> Optional[TicketResponse]:
        return self.tickets.get(ticket_id)
    def list_all(self) -> List[TicketResponse]:
        return list(self.tickets.values())