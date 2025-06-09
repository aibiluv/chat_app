# backend/app/websocket.py
# MODIFIED: Added detailed logging to all methods for better traceability.

import json
import logging
from fastapi import WebSocket
from typing import Dict, List, Set

# Get a logger instance for this module
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Maps user_id to a list of their active WebSocket connections
        self.user_connections: Dict[str, List[WebSocket]] = {}
        # Tracks online status: user_id -> set of conversation_ids they are active in
        self.online_users: Dict[str, Set[str]] = {}

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Sends a message to a single WebSocket connection."""
        await websocket.send_text(message)

    async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str):
        await websocket.accept()
        logger.info(f"WebSocket accepted for user {user_id} in conversation {conversation_id}")
        
        # Inform the new user who is already online in this room
        users_in_this_room = {
            uid for uid, convos in self.online_users.items() if conversation_id in convos
        }
        online_list_message = {
            "type": "online_users_list",
            "user_ids": list(users_in_this_room)
        }
        await self.send_personal_message(json.dumps(online_list_message), websocket)
        logger.debug(f"Sent online user list {users_in_this_room} to user {user_id}")
        
        # Add the new user to all tracking objects
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

        if user_id not in self.online_users:
            self.online_users[user_id] = set()
        self.online_users[user_id].add(conversation_id)
        
        # Broadcast to everyone in the room that a new user has come online
        online_status_message = json.dumps({"type": "status", "user_id": user_id, "status": "online"})
        await self.broadcast(online_status_message, conversation_id)
        logger.info(f"User {user_id} connected. Broadcasted 'online' status to conversation {conversation_id}.")

    async def disconnect(self, websocket: WebSocket, user_id: str, conversation_id: str):
        logger.info(f"Disconnecting user {user_id} from conversation {conversation_id}")
        
        # Get a copy of all conversations the user was active in before disconnection.
        all_user_convos = self.online_users.get(user_id, set()).copy()

        # Remove the specific websocket connection from the conversation room.
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        # Remove the specific websocket from the user's list of connections.
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            # If the user has no more active connections, they are fully offline.
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                if user_id in self.online_users:
                    del self.online_users[user_id]
                
                # Broadcast the "offline" status to ALL conversations the user was in.
                offline_message = json.dumps({"type": "status", "user_id": user_id, "status": "offline"})
                logger.info(f"User {user_id} is now fully offline. Broadcasting to conversations: {all_user_convos}")
                for convo_id in all_user_convos:
                    await self.broadcast(offline_message, convo_id)

    async def broadcast(self, message: str, conversation_id: str):
        if conversation_id in self.active_connections:
            logger.debug(f"Broadcasting to conversation {conversation_id}: {message}")
            for connection in self.active_connections[conversation_id]:
                await connection.send_text(message)

    async def broadcast_to_user(self, user_id: str, message: str):
        """Sends a message to all active connections for a specific user."""
        if user_id in self.user_connections:
            logger.debug(f"Broadcasting to user {user_id}: {message}")
            for connection in self.user_connections[user_id]:
                await connection.send_text(message)

# The singleton instance is created here, making it the single source of truth.
manager = ConnectionManager()
