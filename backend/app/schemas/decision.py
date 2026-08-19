from pydantic import BaseModel, Field


class Decision(BaseModel):

    decision: str = Field(
        description="One of: knowledge, clarification, ticket"
    )

    reason: str = Field(
        description="Reason for the decision"
    )