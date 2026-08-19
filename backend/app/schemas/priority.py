from pydantic import BaseModel, Field


class PriorityAssessment(BaseModel):
    impact: str = Field(description="Business impact")
    urgency: str = Field(description="Urgency")
    priority: str = Field(description="Priority (P1-P5)")
    justification: str = Field(description="Reason for the assigned priority")