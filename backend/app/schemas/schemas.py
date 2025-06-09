
from ..db.models import MessageStatus, Participant
from pydantic import BaseModel, EmailStr, validator
import uuid
from typing import Optional, List
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: uuid.UUID
    avatar_url: Optional[str] = None
    class Config:
        orm_mode = True

class User(BaseModel):
    id: uuid.UUID
    username: str
    class Config:
        orm_mode = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Message Schemas ---
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: uuid.UUID
    status: MessageStatus
    sender: User
    created_at: datetime
    class Config:
        orm_mode = True

# --- Conversation Schemas ---
class ConversationBase(BaseModel):
    name: Optional[str] = None

class ConversationCreate(ConversationBase):
    user_ids: List[uuid.UUID]

class Conversation(ConversationBase):
    id: uuid.UUID
    is_group_chat: bool
    participants: List[User]
    last_message_at: Optional[datetime] = None
    has_unread: bool = False 
    @validator('participants', pre=True, allow_reuse=True)
    def participants_from_relationship(cls, v: List[Participant]) -> List[User]:
        return [participant.user for participant in v]

    class Config:
        orm_mode = True