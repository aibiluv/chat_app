
from fastapi.testclient import TestClient

# The test_client fixture is defined in conftest.py and handles database setup.
def test_register_user_success(test_client: TestClient):
    """
    Test successful user registration.
    """
    response = test_client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "full_name": "Test User"
        },
    )
    # 1. Assert that the request was successful (201 Created)
    assert response.status_code == 201
    
    # 2. Assert that the response body contains the expected user data
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data
    # Ensure the password is not returned in the response
    assert "hashed_password" not in data


def test_register_user_duplicate_username(test_client: TestClient):
    """
    Test that registering with a duplicate username fails.
    """
    # First, create a user
    test_client.post(
        "/auth/register",
        json={"email": "test1@example.com", "username": "duplicateuser", "password": "password123"},
    )
    
    # Then, try to create another user with the same username
    response = test_client.post(
        "/auth/register",
        json={"email": "test2@example.com", "username": "duplicateuser", "password": "password123"},
    )
    
    # Assert that the request failed with a 400 Bad Request status
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already taken"}


def test_login_success(test_client: TestClient):
    """
    Test successful user login and token generation.
    """
    # First, register a user to ensure they exist in the test database
    test_client.post(
        "/auth/register",
        json={"email": "login@example.com", "username": "loginuser", "password": "password123"},
    )

    # Now, attempt to log in with the correct credentials
    login_response = test_client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "password123"},
    )
    
    # 1. Assert that the login was successful
    assert login_response.status_code == 200
    
    # 2. Assert that the response contains an access token
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(test_client: TestClient):
    """
    Test that logging in with an incorrect password fails.
    """
    # Register a user
    test_client.post(
        "/auth/register",
        json={"email": "fail@example.com", "username": "failuser", "password": "password123"},
    )

    # Attempt to log in with the wrong password
    login_response = test_client.post(
        "/auth/login",
        data={"username": "failuser", "password": "wrongpassword"},
    )

    # Assert that the login failed with a 401 Unauthorized status
    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "Incorrect username or password"}
