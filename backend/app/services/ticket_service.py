import uuid
from datetime import datetime, timezone


def _category_code(category: str) -> str:

    letters = [
        word[0]
        for word in category.strip().upper().split()
        if word
    ]

    return "".join(letters) if letters else "TCK"


def create_ticket(
    category: str,
    subcategory: str,
    priority: str,
    impact: str,
    urgency: str,
    justification: str,
    user_query: str,
) -> dict:

    ticket_number = (
        f"{_category_code(category)}-"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    return {
        "ticket_number": ticket_number,
        "category": category,
        "subcategory": subcategory,
        "priority": priority,
        "impact": impact,
        "urgency": urgency,
        "justification": justification,
        "summary": user_query,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
