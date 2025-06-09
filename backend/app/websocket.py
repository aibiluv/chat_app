
import json
from fastapi import WebSocket
from typing import Dict, List, Set


# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: Dict[str, List[WebSocket]] = {}
#         self.user_connections: Dict[str, List[WebSocket]] = {}

#     async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str):
#         await websocket.accept()
#         if conversation_id not in self.active_connections:
#             self.active_connections[conversation_id] = []
#         self.active_connections[conversation_id].append(websocket)
#         if user_id not in self.user_connections:
#             self.user_connections[user_id] = []
#         self.user_connections[user_id].append(websocket)

#     async def disconnect(self, websocket: WebSocket, user_id: str, conversation_id: str):
#         if conversation_id in self.active_connections:
#             if websocket in self.active_connections[conversation_id]:
#                 self.active_connections[conversation_id].remove(websocket)
#             if not self.active_connections[conversation_id]:
#                 del self.active_connections[conversation_id]
#         if user_id in self.user_connections:
#             if websocket in self.user_connections[user_id]:
#                 self.user_connections[user_id].remove(websocket)
#             if not self.user_connections[user_id]:
#                 del self.user_connections[user_id]
    
#     async def broadcast(self, message: str, conversation_id: str):
#         if conversation_id in self.active_connections:
#             for connection in self.active_connections[conversation_id]:
#                 await connection.send_text(message)

#     async def broadcast_to_user(self, user_id: str, message: str):
#         if user_id in self.user_connections:
#             for connection in self.user_connections[user_id]:
#                 await connection.send_text(message)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # This now maps user_id to a list of their active WebSocket connections
        self.user_connections: Dict[str, List[WebSocket]] = {}
        # Tracks online status: user_id -> set of conversation_ids they are active in
        self.online_users: Dict[str, Set[str]] = {}

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Sends a message to a single WebSocket connection."""
        await websocket.send_text(message)

    async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str):
        await websocket.accept()
        
        # Inform the new user who is already online in this room
        users_in_this_room = {
            uid for uid, convos in self.online_users.items() if conversation_id in convos
        }
        online_list_message = {
            "type": "online_users_list",
            "user_ids": list(users_in_this_room)
        }
        await self.send_personal_message(json.dumps(online_list_message), websocket)
        
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
        await self.broadcast(
            json.dumps({"type": "status", "user_id": user_id, "status": "online"}),
            conversation_id
        )

    async def disconnect(self, websocket: WebSocket, user_id: str, conversation_id: str):
        # Remove the specific websocket connection
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        # Remove from user-specific connections
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Update and check the global online status
        is_fully_offline = False
        if user_id in self.online_users:
            if conversation_id in self.online_users[user_id]:
                self.online_users[user_id].remove(conversation_id)
            if not self.online_users[user_id]:
                del self.online_users[user_id]
                is_fully_offline = True

        # Broadcast the offline status to the conversation they just left
        # This informs other users in that specific chat.
        await self.broadcast(
            json.dumps({"type": "status", "user_id": user_id, "status": "offline"}),
            conversation_id
        )

    async def broadcast(self, message: str, conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_text(message)

    async def broadcast_to_user(self, user_id: str, message: str):
        """Sends a message to all active connections for a specific user."""
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                await connection.send_text(message)


manager = ConnectionManager()