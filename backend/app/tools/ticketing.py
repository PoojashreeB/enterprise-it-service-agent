from langchain_core.tools import tool

from app.services.ticket_service import create_ticket as _create_ticket_record


@tool(response_format="content_and_artifact")
def create_ticket(
    category: str,
    subcategory: str,
    priority: str,
    impact: str,
    urgency: str,
    justification: str,
    user_query: str,
) -> tuple[str, dict]:
    """Create an IT service desk ticket for an issue that requires human/IT
    intervention. Only call this when the issue cannot be resolved through
    guidance alone (e.g. it needs hands-on troubleshooting, hardware
    replacement, or access changes only IT staff can make).
    """
    ticket = _create_ticket_record(
        category=category,
        subcategory=subcategory,
        priority=priority,
        impact=impact,
        urgency=urgency,
        justification=justification,
        user_query=user_query,
    )

    content = (
        f"Ticket {ticket['ticket_number']} created "
        f"(priority {priority}, category {category})."
    )

    return content, ticket
