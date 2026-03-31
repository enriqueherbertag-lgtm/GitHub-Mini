from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(Integer, unique=True, nullable=False)
    github_username = Column(String, nullable=False)
    display_name = Column(String)
    avatar_url = Column(String)
    email = Column(String)
    github_token = Column(String)
    is_active = Column(Boolean, default=False)
    affiliation = Column(String)
    languages = Column(ARRAY(String), default=[])
    topics = Column(ARRAY(String), default=[])
    starred_topics = Column(ARRAY(String), default=[])
    embedding = Column(Vector(384))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Debate(Base):
    __tablename__ = "debates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(ARRAY(String), default=[])
    embedding = Column(Vector(384))
    status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DebateParticipation(Base):
    __tablename__ = "debate_participation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    debate_id = Column(UUID(as_uuid=True), ForeignKey("debates.id"), nullable=False)
    type = Column(String)  # 'comment' or 'vote'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    suggested_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score = Column(Float)
    reasons = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
