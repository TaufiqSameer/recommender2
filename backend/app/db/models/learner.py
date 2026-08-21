from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    learner_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    # What the learner wants to achieve.
    goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Example: "backend engineer", "ML engineer", etc.
    target_role: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # Main learning domain.
    domain: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Realistic weekly study commitment.
    weekly_hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Examples:
    # ["projects", "videos", "documentation"]
    learning_preferences: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # Additional constraints/preferences that don't deserve
    # their own columns yet.
    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    aura_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    streak_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class LearnerSkillState(Base):
    __tablename__ = "learner_skill_states"

    learner_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("skill_nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # IRT ability estimate.
    #
    # Roughly:
    # negative -> weak
    # 0       -> average
    # positive -> stronger
    theta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # How certain we are about theta.
    # Range: 0.0 -> 1.0
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Current learning state.
    #
    # locked
    # available
    # learning
    # mastered
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="locked",
    )

    # Number of assessment attempts.
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # A separate mastery value makes the product
    # easier to reason about than relying on theta alone.
    #
    # Range: 0.0 -> 1.0
    mastery: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Evidence collected for this skill.
    #
    # Example:
    # {
    #   "assessment_ids": ["..."],
    #   "project_ids": ["..."],
    #   "observations": ["..."]
    # }
    # evidence: Mapped[dict[str, Any]] = mapped_column(
    #     JSON,
    #     nullable=False,
    #     default=dict,
    # )

    last_assessed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    
class LearnerEvidence(Base):
    __tablename__ = "learner_evidence"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    learner_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("skill_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Where the evidence came from.
    #
    # Examples:
    # assessment
    # checkpoint
    # project
    # tutor_observation
    evidence_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # ID of the assessment/project/checkpoint
    # that produced this evidence.
    source_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Normalized performance score.
    #
    # 0.0 = no demonstrated ability
    # 1.0 = strong demonstrated ability
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Additional information about the evidence.
    #
    # Example:
    # {
    #   "question_id": "rest-q12",
    #   "correct": false,
    #   "difficulty": 2.5
    # }
    evidence_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )