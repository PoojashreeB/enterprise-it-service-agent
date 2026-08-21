from langchain_core.tools import tool


@tool
def lookup_user(username: str) -> str:
    """Look up a corporate user's account status and department in Active
    Directory. Use this only when the request is clearly about a specific
    account.

    NOTE: This is a mock implementation for demo purposes. It does not query
    a real directory service; replace it with a real AD/LDAP integration
    before relying on it.
    """
    return (
        f"[MOCK] User '{username}': status=active, department=Unknown, "
        f"account_locked=False. This is placeholder data — no real "
        f"directory lookup was performed."
    )


@tool(response_format="content_and_artifact")
def reset_password(username: str, reason: str = "") -> tuple[str, dict]:
    """Trigger a self-service password reset email for a corporate Active
    Directory account.

    NOTE: This is a mock implementation for demo purposes. It does not
    perform a real password reset; replace it with a real
    AD/identity-provider integration before relying on it.
    """
    content = (
        f"[MOCK] A password reset email has been queued for '{username}'. "
        f"No real reset was performed."
    )
    artifact = {
        "username": username,
        "reason": reason or "Requested via the chat assistant.",
        "status": "queued",
    }
    return content, artifact
