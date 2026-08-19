from typing import TypedDict


class ServiceDeskState(TypedDict, total=False):

    # User
    user_query: str

    # Classification
    intent: str
    category: str
    subcategory: str
    confidence: float

    # Priority
    impact: str
    urgency: str
    priority: str
    justification: str

    # Decision
    decision: str

    # RAG
    knowledge: str
    retrieved_documents: list

    # Clarification
    clarification_question: str

    # Ticket
    ticket_number: str

    # Final response
    final_response: str