from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    intent: str = Field(description="Type of IT request")
    category: str = Field(description="Main category")
    subcategory: str = Field(description="Subcategory")
    confidence: float = Field(description="Confidence score between 0 and 1")