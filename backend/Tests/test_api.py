from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.main as main_module


# ================================================================
# Health check
# ================================================================

def test_health_check(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "running",
        "application": "Enterprise IT Service Desk Agent",
    }


# ================================================================
# Signup
# ================================================================

def test_signup_creates_user_and_returns_token(client):
    response = client.post(
        "/auth/signup",
        json={"email": "New.User@Example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "new.user@example.com"
    assert body["access_token"]


def test_signup_rejects_duplicate_email(client, signup):
    signup(email="dupe@example.com")

    response = client.post(
        "/auth/signup",
        json={"email": "dupe@example.com", "password": "password123"},
    )

    assert response.status_code == 409


def test_signup_rejects_short_password(client):
    response = client.post(
        "/auth/signup",
        json={"email": "shortpw@example.com", "password": "short"},
    )

    assert response.status_code == 422


# ================================================================
# Login
# ================================================================

def test_login_with_correct_credentials(client, signup):
    signup(email="loginuser@example.com", password="password123")

    response = client.post(
        "/auth/login",
        json={"email": "loginuser@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "loginuser@example.com"


def test_login_with_wrong_password(client, signup):
    signup(email="wrongpw@example.com", password="password123")

    response = client.post(
        "/auth/login",
        json={"email": "wrongpw@example.com", "password": "not-the-password"},
    )

    assert response.status_code == 401


def test_login_with_unknown_email(client):
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )

    assert response.status_code == 401


# ================================================================
# /auth/me
# ================================================================

def test_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_delete_me_removes_account(client, auth_headers):
    response = client.delete("/auth/me", headers=auth_headers)
    assert response.status_code == 204

    follow_up = client.get("/auth/me", headers=auth_headers)
    assert follow_up.status_code == 401


# ================================================================
# Conversations
# ================================================================

def test_list_conversations_requires_authentication(client):
    response = client.get("/conversations")

    assert response.status_code == 401


def test_create_and_list_conversation(client, auth_headers):
    create_response = client.post("/conversations", headers=auth_headers)
    assert create_response.status_code == 200
    conversation = create_response.json()
    assert conversation["title"] == "New conversation"

    list_response = client.get("/conversations", headers=auth_headers)
    assert list_response.status_code == 200
    ids = [item["id"] for item in list_response.json()]
    assert conversation["id"] in ids


def test_get_conversation_detail_includes_messages(client, auth_headers):
    conversation = client.post("/conversations", headers=auth_headers).json()

    response = client.get(f"/conversations/{conversation['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["messages"] == []


def test_get_conversation_not_found(client, auth_headers):
    response = client.get("/conversations/does-not-exist", headers=auth_headers)

    assert response.status_code == 404


def test_get_conversation_owned_by_another_user_is_not_found(client, signup):
    first_user_headers = {
        "Authorization": f"Bearer {signup(email='owner@example.com')['access_token']}"
    }
    conversation = client.post("/conversations", headers=first_user_headers).json()

    other_user_headers = {
        "Authorization": f"Bearer {signup(email='intruder@example.com')['access_token']}"
    }
    response = client.get(f"/conversations/{conversation['id']}", headers=other_user_headers)

    assert response.status_code == 404


def test_delete_conversation(client, auth_headers):
    conversation = client.post("/conversations", headers=auth_headers).json()

    delete_response = client.delete(f"/conversations/{conversation['id']}", headers=auth_headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/conversations/{conversation['id']}", headers=auth_headers)
    assert get_response.status_code == 404


# ================================================================
# /service-desk
# ================================================================

def _fake_graph_result(**overrides):
    result = {
        "intent": "reset_password",
        "category": "Access Management",
        "subcategory": "Password Reset",
        "priority": "P3",
        "decision": "knowledge",
        "ticket_number": None,
        "final_response": "Here is how you can reset your password.",
    }
    result.update(overrides)
    return result


def test_service_desk_requires_authentication(client):
    response = client.post("/service-desk", json={"message": "I forgot my password"})

    assert response.status_code == 401


def test_service_desk_creates_new_conversation(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        main_module,
        "graph",
        SimpleNamespace(invoke=lambda state: _fake_graph_result()),
    )

    response = client.post(
        "/service-desk",
        json={"message": "I forgot my password"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["final_response"] == "Here is how you can reset your password."
    assert body["conversation_id"]

    conversations = client.get("/conversations", headers=auth_headers).json()
    assert any(item["id"] == body["conversation_id"] for item in conversations)

    detail = client.get(f"/conversations/{body['conversation_id']}", headers=auth_headers).json()
    roles = [message["role"] for message in detail["messages"]]
    assert roles == ["user", "agent"]
    assert detail["messages"][0]["content"] == "I forgot my password"
    assert detail["messages"][1]["content"] == "Here is how you can reset your password."


def test_service_desk_appends_to_existing_conversation(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        main_module,
        "graph",
        SimpleNamespace(invoke=lambda state: _fake_graph_result()),
    )

    conversation = client.post("/conversations", headers=auth_headers).json()

    response = client.post(
        "/service-desk",
        json={"message": "Follow-up question", "conversation_id": conversation["id"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == conversation["id"]

    detail = client.get(f"/conversations/{conversation['id']}", headers=auth_headers).json()
    assert len(detail["messages"]) == 2


def test_service_desk_with_unknown_conversation_id_returns_404(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        main_module,
        "graph",
        SimpleNamespace(invoke=lambda state: _fake_graph_result()),
    )

    response = client.post(
        "/service-desk",
        json={"message": "Hello", "conversation_id": "does-not-exist"},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_service_desk_with_another_users_conversation_returns_404(client, signup, monkeypatch):
    monkeypatch.setattr(
        main_module,
        "graph",
        SimpleNamespace(invoke=lambda state: _fake_graph_result()),
    )

    owner_headers = {
        "Authorization": f"Bearer {signup(email='deskowner@example.com')['access_token']}"
    }
    conversation = client.post("/conversations", headers=owner_headers).json()

    intruder_headers = {
        "Authorization": f"Bearer {signup(email='deskintruder@example.com')['access_token']}"
    }
    response = client.post(
        "/service-desk",
        json={"message": "Hello", "conversation_id": conversation["id"]},
        headers=intruder_headers,
    )

    assert response.status_code == 404


# ================================================================
# Unhandled exceptions
# ================================================================

def test_unhandled_exception_returns_json_error(client, auth_headers, monkeypatch):
    def raise_error(state):
        raise ValueError("Upstream error: Service temporarily overloaded")

    monkeypatch.setattr(main_module, "graph", SimpleNamespace(invoke=raise_error))

    # A real ASGI server (or a browser hitting the deployed API) only ever
    # sees the JSON response our handler sends - it has no way to "re-raise"
    # the exception. TestClient's default raise_server_exceptions=True exists
    # purely to surface bugs during test authoring, so it's disabled here to
    # observe the same response a real client would get.
    lenient_client = TestClient(main_module.app, raise_server_exceptions=False)

    response = lenient_client.post(
        "/service-desk",
        json={"message": "Hello"},
        headers=auth_headers,
    )

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert "detail" in response.json()
