"""
Enterprise Agent AI — Database Models

SQLAlchemy ORM models for documents, conversations, and audit logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.core.database import Base


class Document(Base):
    """Stored document for RAG retrieval."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False, default=0)
    total_chunks = Column(Integer, nullable=False, default=1)
    embedding = Column(Vector(1536))  # pgvector column
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, chunk={self.chunk_index})>"


class Conversation(Base):
    """Agent conversation history."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model_used = Column(String(100))
    provider = Column(String(50))
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, agent={self.agent_type})>"


class AuditLog(Base):
    """Audit trail for all agent operations."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))
    user_id = Column(String(100))
    details = Column(JSON, default=dict)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action})>"
