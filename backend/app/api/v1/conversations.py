
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ...cruds import chat_crud
from ...schemas import schemas
from ...db import database, models
from ...core.security import get_current_user
from ...websocket import manager
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.Conversation)
def create_new_conversation(
    conversation: schemas.ConversationCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    return chat_crud.create_conversation(db=db, conversation=conversation, creator_id=current_user.id)

@router.get("/", response_model=List[schemas.Conversation])
def read_user_conversations(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    return chat_crud.get_user_conversations(db=db, user_id=current_user.id)

@router.get("/{conversation_id}/messages", response_model=List[schemas.Message])
def read_conversation_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not chat_crud.is_user_participant(db, user_id=current_user.id, conversation_id=conversation_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a participant of this conversation")
    return chat_crud.get_conversation_messages(db=db, conversation_id=conversation_id)


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    conversation_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Marks messages as read and broadcasts read receipts to senders."""
    read_receipts = chat_crud.mark_conversation_as_read(db, user_id=current_user.id, conversation_id=conversation_id)
    
    # After marking as read, broadcast the updates to the relevant senders
    for sender_id, message_ids in read_receipts.items():
        receipt_message = {
            "type": "messages_read",
            "conversation_id": str(conversation_id),
            "message_ids": message_ids
        }
        # Broadcast to all connections of the sender
        await manager.broadcast_to_user(sender_id, json.dumps(receipt_message))
        logger.info(f"sender: {sender_id}")

    return