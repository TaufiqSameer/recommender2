from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LearningActivity(Base):

    __tablename__ = "learning_activities"

    # =====================================================
    # IDENTITY
    # =====================================================

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    # =====================================================
    # LEARNER
    # =====================================================

    learner_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # =====================================================
    # SKILL
    # =====================================================

    skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skill_nodes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # =====================================================
    # ACTIVITY CONTENT
    # =====================================================

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    objective: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    difficulty: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    hints: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # =====================================================
    # RECOMMENDER CONTEXT
    # =====================================================

    recommendation_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # =====================================================
    # GENERATION
    # =====================================================

    generation_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="llm",
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )