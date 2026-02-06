import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
import uuid

client = TestClient(app)

# Helper to generate unique users for tests
def generate_user():
    random_str = str(uuid.uuid4())[:8]
    return {
        "username": f"test_user_{random_str}",
        "password": "securepassword123"
    }

# --- 1. AUTHENTICATION TESTS ---

def test_register_user():
    user_data = generate_user()
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert "id" in data

def test_login_user():
    # 1. Register first
    user_data = generate_user()
    client.post("/auth/register", json=user_data)
    
    # 2. Try to Login
    response = client.post("/auth/login", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post("/auth/login", json={
        "username": "non_existent_user",
        "password": "wrongpassword"
    })
    assert response.status_code == 500 or response.status_code == 401 # Depends on your error handling

# --- 2. PROTECTED ROUTES TESTS ---

def test_access_history_unauthorized():
    """Try to access protected route without token"""
    response = client.get("/history")
    assert response.status_code == 403 # HTTPBearer returns 403 when missing

def test_rag_query_mocked():
    """
    Tests the /query endpoint by MOCKING the actual AI chain.
    This ensures CI doesn't fail due to Google API quotas or network issues.
    """
    # 1. Get Token
    user_data = generate_user()
    client.post("/auth/register", json=user_data)
    login_res = client.post("/auth/login", json=user_data)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Mock the 'query_rag' function inside app.routes.query
    # We force it to return specific values instead of calling Gemini
    with patch("app.routes.query.query_rag") as mock_rag:
        # Define what the mock returns: (answer, time, num_vectors)
        mock_rag.return_value = ("This is a mocked AI response.", 0.5, 3)

        # 3. Call Endpoint
        response = client.post("/query", json={"question": "Test question"}, headers=headers)
        
        # 4. Verify
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a mocked AI response."
        assert data["cluster"] is None or isinstance(data["cluster"], int)

def test_get_history_authorized():
    """Test getting history after making a query"""
    # 1. Setup User & Token
    user_data = generate_user()
    client.post("/auth/register", json=user_data)
    token = client.post("/auth/login", json=user_data).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Mock & Create a Query entry
    with patch("app.routes.query.query_rag") as mock_rag:
        mock_rag.return_value = ("History Answer", 0.1, 2)
        client.post("/query", json={"question": "History Q"}, headers=headers)

    # 3. Fetch History
    response = client.get("/history", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Check if our query is in the history
    assert "history" in data
    assert len(data["history"]) > 0
    assert data["history"][0]["question"] == "History Q"