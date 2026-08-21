from datetime import datetime

from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    category: str = Field(min_length=1)
    subcategory: str = ""
    priority: str = "P3"
    summary: str = Field(min_length=1)


class TicketOut(BaseModel):
    id: str
    ticket_number: str
    category: str
    subcategory: str
    priority: str
    impact: str
    urgency: str
    justification: str
    summary: str
    status: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PasswordResetCreateRequest(BaseModel):
    username: str = Field(min_length=1)
    reason: str = ""


class PasswordResetOut(BaseModel):
    id: str
    username: str
    reason: str
    status: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
