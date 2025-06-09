from ..core.security import decrypt_message, encrypt_message
from sqlalchemy.orm import Session
from ..schemas import schemas
from ..db import models
import uuid
from datetime import datetime
from sqlalchemy import and_, func, update
from datetime import datetime, timezone 

def create_conversation(db: Session, conversation: schemas.ConversationCreate, creator_id: uuid.UUID):
    # Check for existing 1-on-1 conversation to prevent duplicates
    if len(conversation.user_ids) == 1:
        other_user_id = conversation.user_ids[0]
        # Query for a non-group conversation that has exactly 2 participants,
        # and those participants are the current user and the other user.
        existing_convo = db.query(models.Conversation)\
            .join(models.Participant)\
            .filter(models.Conversation.is_group_chat == False)\
            .group_by(models.Conversation.id)\
            .having(and_(
                func.count(models.Participant.user_id) == 2,
                func.bool_and(models.Participant.user_id.in_([creator_id, other_user_id]))
            )).first()
        
        if existing_convo:
            return existing_convo

    # If no existing convo, or if it's a group chat, create a new one
    db_convo = models.Conversation(
        name=conversation.name,
        is_group_chat=len(conversation.user_ids) > 1
    )
    db.add(db_convo)
    db.commit()
    db.refresh(db_convo)

    # Add participants
    all_user_ids = set(conversation.user_ids + [creator_id])
    for user_id in all_user_ids:
        db_participant = models.Participant(user_id=user_id, conversation_id=db_convo.id)
        db.add(db_participant)
    
    db.commit()
    db.refresh(db_convo)
    return db_convo


def get_user_conversations(db: Session, user_id: uuid.UUID):
    user_conversations = db.query(models.Conversation).join(models.Participant).filter(models.Participant.user_id == user_id).all()
    aware_min_dt = datetime.min.replace(tzinfo=timezone.utc)
    for convo in user_conversations:
        participant_entry = db.query(models.Participant).filter(
            models.Participant.user_id == user_id,
            models.Participant.conversation_id == convo.id
        ).first()
        # normalize both sides to UTC‐aware
        last_read_raw    = participant_entry.last_read_timestamp
        last_message_raw = convo.last_message_at

        last_read    = _ensure_aware(last_read_raw)    or aware_min_dt
        last_message = _ensure_aware(last_message_raw) or aware_min_dt

        convo.has_unread = (last_message > last_read)

    return user_conversations


def mark_conversation_as_read(db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID):
    # Update the user's last_read_timestamp for this conversation
    db.query(models.Participant).filter(
        models.Participant.user_id == user_id,
        models.Participant.conversation_id == conversation_id
    ).update({"last_read_timestamp":  datetime.now(timezone.utc)})
    
    # Find all messages in this conversation not sent by the current user
    # and update their status to 'read'
    stmt = (
        update(models.Message)
        .where(
            models.Message.conversation_id == conversation_id,
            models.Message.sender_id != user_id,
            models.Message.status != models.MessageStatus.read
        )
        .values(status=models.MessageStatus.read)
        .returning(models.Message.id, models.Message.sender_id)
    )
    
    updated_messages = db.execute(stmt).fetchall()
    db.commit()
    
    # Return a structure mapping sender_id to a list of their message_ids that were just read
    read_receipts = {}
    for msg_id, sender_id in updated_messages:
        sender_id_str = str(sender_id)
        if sender_id_str not in read_receipts:
            read_receipts[sender_id_str] = []
        read_receipts[sender_id_str].append(str(msg_id))
        
    return read_receipts

def get_conversation_messages(db: Session, conversation_id: uuid.UUID, skip: int = 0, limit: int = 100):
    messages = db.query(models.Message).filter(models.Message.conversation_id == conversation_id).order_by(models.Message.created_at.asc()).offset(skip).limit(limit).all()
    for msg in messages:
        msg.content = decrypt_message(msg.content)
        print(f"msg {msg.content} ")
    return messages


def is_user_participant(db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID) -> bool:
    """Check if a user is a participant in a conversation."""
    return db.query(models.Participant).filter(
        models.Participant.user_id == user_id,
        models.Participant.conversation_id == conversation_id
    ).first() is not None
# --- Message CRUD ---
def create_message(db: Session, message: schemas.MessageCreate, sender_id: uuid.UUID, conversation_id: uuid.UUID):
    encrypted_content = encrypt_message(message.content)
    db_message = models.Message(
        content=encrypted_content,
        sender_id=sender_id,
        conversation_id=conversation_id
    )
    db.add(db_message)
    
    # Update conversation's last_message_at timestamp
    db.query(models.Conversation).filter(models.Conversation.id == conversation_id).update({"last_message_at": datetime.utcnow()})
    
    db.commit()
    db.refresh(db_message)
    return db_message


def _ensure_aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)