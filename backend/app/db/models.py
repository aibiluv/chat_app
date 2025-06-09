
import uuid
from sqlalchemy import Boolean, Column, String, Text, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class MessageStatus(enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    avatar_url = Column(String, nullable=True)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True) # For group chats
    is_group_chat = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_message_at = Column(TIMESTAMP(timezone=True), nullable=True)

    participants = relationship("Participant", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")

class Participant(Base):
    __tablename__ = "participants"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), primary_key=True)
    
    user = relationship("User")
    conversation = relationship("Conversation", back_populates="participants")
    last_read_timestamp = Column(TIMESTAMP(timezone=True), default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    status = Column(Enum(MessageStatus), default=MessageStatus.sent, nullable=False)
    sender = relationship("User")
    conversation = relationship("Conversation", back_populates="messages")