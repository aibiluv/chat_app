from fastapi.testclient import TestClient
from typing import Dict

# This is a helper function to reduce boilerplate code in tests.
# It handles logging in a user and returning the authorization headers.
def get_auth_headers(client: TestClient, username: str, password: str = "password123") -> Dict[str, str]:
    """Logs in a user and returns authorization headers."""
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, f"Failed to log in user {username}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_get_one_on_one_conversation(test_client: TestClient):
    """
    Test creating a 1-on-1 conversation and then fetching it.
    """
    # 1. Create two users needed for the conversation.
    user_a_res = test_client.post("/auth/register", json={"email": "alice@test.com", "username": "alice", "password": "password123"})
    assert user_a_res.status_code == 201
    user_a_id = user_a_res.json()["id"]

    user_b_res = test_client.post("/auth/register", json={"email": "bob@test.com", "username": "bob", "password": "password123"})
    assert user_b_res.status_code == 201
    user_b_id = user_b_res.json()["id"]

    # 2. Log in as User A to get an auth token.
    auth_headers = get_auth_headers(test_client, "alice")

    # 3. As User A, create a new conversation with User B.
    create_convo_res = test_client.post(
        "/conversations/",
        json={"user_ids": [user_b_id]},
        headers=auth_headers
    )
    assert create_convo_res.status_code == 200
    
    convo_data = create_convo_res.json()
    assert convo_data["is_group_chat"] is False
    # Verify that both users are correctly listed as participants.
    participant_usernames = {p["username"] for p in convo_data["participants"]}
    assert "alice" in participant_usernames
    assert "bob" in participant_usernames

    # 4. As User A, fetch the list of conversations.
    get_convos_res = test_client.get("/conversations/", headers=auth_headers)
    assert get_convos_res.status_code == 200
    
    convos_list = get_convos_res.json()
    assert len(convos_list) == 1
    assert convos_list[0]["id"] == convo_data["id"]


def test_create_group_conversation(test_client: TestClient):
    """
    Test creating a group conversation with multiple participants.
    """
    # 1. Create three users for the group chat.
    test_client.post("/auth/register", json={"email": "carol@test.com", "username": "carol", "password": "password123"})
    dave_res = test_client.post("/auth/register", json={"email": "dave@test.com", "username": "dave", "password": "password123"})
    eve_res = test_client.post("/auth/register", json={"email": "eve@test.com", "username": "eve", "password": "password123"})
    
    dave_id = dave_res.json()["id"]
    eve_id = eve_res.json()["id"]
    
    # 2. Log in as Carol.
    auth_headers = get_auth_headers(test_client, "carol")

    # 3. As Carol, create a group chat with Dave and Eve.
    create_convo_res = test_client.post(
        "/conversations/",
        json={
            "user_ids": [dave_id, eve_id],
            "name": "Test Group"
        },
        headers=auth_headers
    )
    assert create_convo_res.status_code == 200
    
    convo_data = create_convo_res.json()
    assert convo_data["is_group_chat"] is True
    assert convo_data["name"] == "Test Group"
    participant_usernames = {p["username"] for p in convo_data["participants"]}
    assert participant_usernames == {"carol", "dave", "eve"}


def test_cannot_get_messages_from_unrelated_conversation(test_client: TestClient):
    """
    Test that a user receives a 403 Forbidden error when trying to access
    a conversation they are not a part of.
    """
    # 1. User A and B create a private conversation.
    user_a_res = test_client.post("/auth/register", json={"email": "private_a@test.com", "username": "private_a", "password": "password123"})
    user_b_res = test_client.post("/auth/register", json={"email": "private_b@test.com", "username": "private_b", "password": "password123"})
    user_b_id = user_b_res.json()["id"]

    auth_headers_a = get_auth_headers(test_client, "private_a")
    convo_res = test_client.post("/conversations/", json={"user_ids": [user_b_id]}, headers=auth_headers_a)
    convo_id = convo_res.json()["id"]

    # 2. A third user, the Intruder, is created.
    test_client.post("/auth/register", json={"email": "intruder@test.com", "username": "intruder", "password": "password123"})
    
    # 3. The Intruder logs in.
    auth_headers_intruder = get_auth_headers(test_client, "intruder")

    # 4. The Intruder attempts to fetch messages from the private conversation.
    get_messages_res = test_client.get(f"/conversations/{convo_id}/messages", headers=auth_headers_intruder)
    
    # 5. Assert that the request was forbidden.
    assert get_messages_res.status_code == 403
    assert get_messages_res.json() == {"detail": "User is not a participant of this conversation"}

