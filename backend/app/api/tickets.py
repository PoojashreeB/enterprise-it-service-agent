from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.database import Ticket, User
from app.schemas.service_desk import TicketCreateRequest, TicketOut
from app.services.ticket_service import create_ticket as create_ticket_record

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketOut])
def list_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )


@router.post("", response_model=TicketOut)
def create_ticket(
    payload: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket_data = create_ticket_record(
        category=payload.category,
        subcategory=payload.subcategory,
        priority=payload.priority,
        impact="",
        urgency="",
        justification="Manually raised by the user.",
        user_query=payload.summary,
    )

    ticket = Ticket(
        user_id=current_user.id,
        ticket_number=ticket_data["ticket_number"],
        category=payload.category,
        subcategory=payload.subcategory,
        priority=payload.priority,
        impact="",
        urgency="",
        justification="Manually raised by the user.",
        summary=payload.summary,
        status="open",
        source="manual",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.user_id == current_user.id)
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
        )
    return ticket
