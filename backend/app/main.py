import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import auth as auth_router
from app.api import conversations as conversations_router
from app.api import tickets as tickets_router
from app.api.deps import get_current_user
from app.core.db import Base, engine, get_db
from app.graph.workflow import build_service_desk_graph
from app.models.database import Conversation, Message, Ticket, User

logger = logging.getLogger(__name__)

graph = build_service_desk_graph()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Enterprise IT Service Desk Agent",
    version="1.0",
    lifespan=lifespan,
)

app.include_router(auth_router.router)
app.include_router(conversations_router.router)
app.include_router(tickets_router.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception while processing %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": (
                "Something went wrong processing your request. Please try again."
            )
        },
    )


class ServiceDeskRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@app.get("/")
def health():
    return {
        "status": "running",
        "application": "Enterprise IT Service Desk Agent"
    }


@app.post("/service-desk")
def service_desk(
    request: ServiceDeskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = request.message.strip()

    if request.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=message[:60] or "New conversation",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    db.add(Message(conversation_id=conversation.id, role="user", content=message))
    db.commit()

    state = {"user_query": message}
    result = graph.invoke(state)

    db.add(
        Message(
            conversation_id=conversation.id,
            role="agent",
            content=result.get("final_response", ""),
            meta={
                "category": result.get("category"),
                "subcategory": result.get("subcategory"),
                "priority": result.get("priority"),
                "decision": result.get("decision"),
                "ticket_number": result.get("ticket_number"),
            },
        )
    )

    ticket_artifact = result.get("ticket")
    if ticket_artifact:
        db.add(
            Ticket(
                user_id=current_user.id,
                conversation_id=conversation.id,
                ticket_number=ticket_artifact.get("ticket_number", ""),
                category=ticket_artifact.get("category", ""),
                subcategory=ticket_artifact.get("subcategory", ""),
                priority=ticket_artifact.get("priority", ""),
                impact=ticket_artifact.get("impact", ""),
                urgency=ticket_artifact.get("urgency", ""),
                justification=ticket_artifact.get("justification", ""),
                summary=ticket_artifact.get("summary", ""),
                status="open",
                source="agent",
            )
        )

    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()

    result["conversation_id"] = conversation.id
    return result
