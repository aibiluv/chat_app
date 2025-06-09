# Main application entry point.

import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .db import models, database
from .api.v1 import auth, conversations, user
from .websocket import manager
import json
from .schemas import schemas
from .cruds import user_crud, chat_crud
from .core.security import get_user_from_token
import uuid

logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    logger.info("Application startup: Creating database tables...")
    # Create all database tables based on the models
    # In a real production app, you would use Alembic for migrations.
    #models.Base.metadata.drop_all(bind=database.engine)

    models.Base.metadata.create_all(bind=database.engine)
    yield
    # On shutdown (if needed)
    logger.info("Application shutdown.")




app = FastAPI(
    title="ChatFlow API",
    description="The backend API for the ChatFlow messaging application.",
    version="0.1.0"
)

# --- Middleware ---
# Configure CORS to allow the frontend to communicate with the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # The origin of our React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# Include routers for different parts of the API for better organization.
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
app.include_router(user.router, prefix="/users", tags=["users"])



@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok"}




@app.websocket("/ws/{conversation_id}/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str,
):
    db = database.SessionLocal()
    try:
        user = get_user_from_token(db, token)
        if not user:
            await websocket.close(code=1008)
            return

        convo_uuid = uuid.UUID(conversation_id)
        if not chat_crud.is_user_participant(db, user_id=user.id, conversation_id=convo_uuid):
            logger.debug(f"participant not in conversation, {user.id} :{conversation_id}")
            await websocket.close(code=1011)
            return

        await manager.connect(websocket, str(user.id), conversation_id)
        while True:
            data = await websocket.receive_text()
            
            message = schemas.MessageCreate(content=data)
            db_message = chat_crud.create_message(db, message, user.id, convo_uuid)
            # Case were messages were not saving in db but getting sent to user.
            if not db_message:
                logger.debug("Message couldn't save so we do not want to send it.")
                # Handle case where message fails to save
                await websocket.send_text(json.dumps({"type": "error", "content": "Message failed to send"}))
                continue

            broadcast_message = {
                "id": str(db_message.id),
                "sender": { "id": str(user.id), "username": user.username },
                "content": message.content,
                "created_at": db_message.created_at.isoformat(),
                "conversation_id": str(db_message.conversation_id),
                "status": db_message.status.value
            }
            logger.info("Broadcasting!!!")
            await manager.broadcast(json.dumps(broadcast_message), conversation_id)

    except WebSocketDisconnect:
            logger.error("disconnecting: ")
            if user:
                logger.info(f"disconnecting: user: {user.id} ")
                await manager.disconnect(websocket, str(user.id), conversation_id)
    except Exception as e:
        if user:
            logger.error(f"Something happened: {e}")
            await manager.disconnect(websocket, str(user.id), conversation_id)
    finally:
        db.close()