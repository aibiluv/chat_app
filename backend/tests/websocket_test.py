
import pytest
import json
from unittest.mock import AsyncMock

# The pytest.ini file ensures this import works correctly
from app.websocket import ConnectionManager

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio


@pytest.fixture
def manager() -> ConnectionManager:
    """Returns a clean ConnectionManager instance for each test."""
    # Reset the singleton manager's state before each test
    manager_instance = ConnectionManager()
    manager_instance.active_connections.clear()
    manager_instance.user_connections.clear()
    manager_instance.online_users.clear()
    return manager_instance


async def test_connect(manager: ConnectionManager):
    """
    Test that the connect method correctly adds a user and broadcasts their online status.
    """
    mock_websocket = AsyncMock()
    user_id = "user1"
    conversation_id = "convo1"

    await manager.connect(mock_websocket, user_id, conversation_id)

    # 1. Assert that the user was added to all tracking dictionaries
    assert conversation_id in manager.active_connections
    assert mock_websocket in manager.active_connections[conversation_id]
    assert user_id in manager.user_connections
    assert mock_websocket in manager.user_connections[user_id]
    
    # 2. Assert that the 'accept' method was called on the websocket
    mock_websocket.accept.assert_awaited_once()

    # 3. Assert that the initial list of online users was sent (should be empty)
    expected_online_list = json.dumps({"type": "online_users_list", "user_ids": []})
    mock_websocket.send_text.assert_any_await(expected_online_list)
    
    # 4. Assert that the "online" status was broadcast
    expected_status_message = json.dumps({"type": "status", "user_id": user_id, "status": "online"})
    # The broadcast message should also be sent to the connected user
    mock_websocket.send_text.assert_any_await(expected_status_message)


async def test_disconnect_broadcasts_to_other_users(manager: ConnectionManager):
    """
    Test that when a user disconnects, the offline status is broadcast to other users
    in the same conversation.
    """
    convo_id = "convo1"
    user_a_id = "user_a"
    user_b_id = "user_b"

    # Mock websockets for two different users
    ws_a = AsyncMock()
    ws_b = AsyncMock()

    # Connect both users to the same conversation
    await manager.connect(ws_a, user_a_id, convo_id)
    await manager.connect(ws_b, user_b_id, convo_id)
    
    # Reset mock for ws_a to ignore the connection calls
    ws_a.reset_mock()

    # Now, disconnect User B
    await manager.disconnect(ws_b, user_b_id, convo_id)

    # 1. Assert that User B's data is removed from the manager
    assert convo_id in manager.active_connections
    assert ws_b not in manager.active_connections[convo_id]
    assert user_b_id not in manager.user_connections
    assert user_b_id not in manager.online_users

    # 2. Assert that User A's data is still present
    assert user_a_id in manager.user_connections
    assert ws_a in manager.active_connections[convo_id]

    # 3. Assert that User A (the remaining user) received the broadcast that User B is offline
    expected_offline_message = json.dumps({"type": "status", "user_id": user_b_id, "status": "offline"})
    ws_a.send_text.assert_awaited_once_with(expected_offline_message)


async def test_connect_informs_about_existing_users(manager: ConnectionManager):
    """
    Test that a new user is correctly informed about users who are already online.
    """
    # User A is already online
    user_a_ws = AsyncMock()
    await manager.connect(user_a_ws, "user_a", "convo1")

    # Now, User B connects
    user_b_ws = AsyncMock()
    await manager.connect(user_b_ws, "user_b", "convo1")

    # Assert that User B received a list containing User A's ID
    expected_online_list = json.dumps({"type": "online_users_list", "user_ids": ["user_a"]})
    user_b_ws.send_text.assert_any_await(expected_online_list)
