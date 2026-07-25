# =============================================================================
# backend/tests/test_auth.py
#
# Unit tests for the authentication services and endpoints.
# =============================================================================

import pytest
from services.auth_service import verify_password, get_password_hash, create_access_token, decode_token

def test_password_hashing():
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_creation_and_decoding():
    data = {"sub": "1", "role": "Admin"}
    token = create_access_token(data=data)
    
    decoded = decode_token(token)
    assert decoded["sub"] == "1"
    assert decoded["role"] == "Admin"
    assert "exp" in decoded

# To test the actual endpoints, we would use FastAPI TestClient with a mocked AsyncSession.
# For brevity in this MVP, we focus on the core auth service logic.
