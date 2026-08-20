from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core import security
from app.core.config import settings


# ================================================================
# Password hashing
# ================================================================

def test_hash_password_round_trips_with_verify_password():
    stored = security.hash_password("correct-horse-battery-staple")

    assert security.verify_password("correct-horse-battery-staple", stored) is True


def test_verify_password_rejects_wrong_password():
    stored = security.hash_password("correct-horse-battery-staple")

    assert security.verify_password("wrong-password", stored) is False


def test_hash_password_uses_a_random_salt_each_time():
    first = security.hash_password("same-password")
    second = security.hash_password("same-password")

    assert first != second
    assert security.verify_password("same-password", first) is True
    assert security.verify_password("same-password", second) is True


@pytest.mark.parametrize(
    "stored",
    [
        "not-in-the-expected-format",
        "260000$only-two-parts",
        "",
    ],
)
def test_verify_password_returns_false_for_malformed_stored_value(stored):
    assert security.verify_password("anything", stored) is False


# ================================================================
# JWT access tokens
# ================================================================

def test_create_access_token_round_trips_with_decode_access_token():
    token = security.create_access_token("user-123")

    assert security.decode_access_token(token) == "user-123"


def test_decode_access_token_returns_none_for_garbage_token():
    assert security.decode_access_token("not-a-real-token") is None


def test_decode_access_token_returns_none_for_wrong_secret():
    payload = {
        "sub": "user-123",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, "a-completely-different-secret", algorithm=settings.jwt_algorithm)

    assert security.decode_access_token(token) is None


def test_decode_access_token_returns_none_for_expired_token():
    payload = {
        "sub": "user-123",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    assert security.decode_access_token(token) is None
