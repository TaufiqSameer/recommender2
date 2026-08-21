from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
)

from app.db.database import Base
from app.domain.verification import VerificationStatus


class KnowledgeCandidate(Base):

    __tablename__ = "knowledge_candidates"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    concept = Column(
        String(200),
        nullable=False,
        index=True,
    )

    domain = Column(
        String(100),
        nullable=True,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    proposed_relationships = Column(
        JSON,
        nullable=False,
        default=list,
    )

    sources = Column(
        JSON,
        nullable=False,
        default=list,
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    verification_status = Column(
        String(30),
        nullable=False,
        default=VerificationStatus.PENDING_REVIEW.value,
    )

    rejection_reason = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )