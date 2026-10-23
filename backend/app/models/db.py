import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value


class UniversalJSON(TypeDecorator):
    """Platform-independent JSON type (JSONB on PostgreSQL, standard JSON/Text on SQLite)."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        import sqlalchemy
        return dialect.type_descriptor(sqlalchemy.JSON())


class User(Base):
    """Users table."""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    runs = relationship("Run", back_populates="user", cascade="all, delete-orphan")


class Run(Base):
    """Runs table."""
    __tablename__ = "runs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    idea = Column(Text, nullable=False)
    status = Column(
        String(20),
        CheckConstraint("status IN ('queued','running','completed','failed','cancelled')"),
        nullable=False,
        default="queued"
    )
    options = Column(UniversalJSON, default=dict)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(8, 4), default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="runs")
    outputs = relationship("AgentOutput", back_populates="run", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="run", cascade="all, delete-orphan")
    debate_messages = relationship("DebateMessage", back_populates="run", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_runs_user_created", "user_id", "created_at"),
    )


class AgentOutput(Base):
    """Agent deliverables by version."""
    __tablename__ = "agent_outputs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID(), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    agent = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    output = Column(UniversalJSON, nullable=False)
    tokens = Column(Integer, nullable=True, default=0)
    latency_ms = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="outputs")

    __table_args__ = (
        UniqueConstraint("run_id", "agent", "version", name="uq_run_agent_version"),
        Index("idx_outputs_run", "run_id"),
    )


class Score(Base):
    """CEO / Critic scores and reviews."""
    __tablename__ = "scores"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID(), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    target_agent = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    score = Column(Numeric(3, 1), nullable=False)
    feedback = Column(UniversalJSON, nullable=True)
    passed = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="scores")

    __table_args__ = (
        Index("idx_scores_run", "run_id"),
    )


class DebateMessage(Base):
    """Debate exchanges between agents."""
    __tablename__ = "debate_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID(), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    round = Column(Integer, nullable=False)
    from_agent = Column(Text, nullable=False)
    to_agent = Column(Text, nullable=False)
    content = Column(UniversalJSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="debate_messages")

    __table_args__ = (
        Index("idx_debate_run_round", "run_id", "round"),
    )


class Export(Base):
    """Generated exports (PDF, PPTX, Markdown)."""
    __tablename__ = "exports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID(), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    format = Column(String(10), nullable=False)  # pdf, pptx, md
    path = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="exports")
