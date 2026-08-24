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


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skill_nodes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Overall assessment difficulty.
    difficulty: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    # How the assessment was generated.
    #
    # Examples:
    # "llm"
    # "manual"
    # "hybrid"
    generation_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="llm",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    assessment_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "assessments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skill_nodes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Example:
    # "What does HTTP status code 404 mean?"
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Examples:
    # "multiple_choice"
    # "true_false"
    # "short_answer"
    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Flexible question data.
    #
    # Multiple choice example:
    #
    # {
    #     "options": [
    #         "Created",
    #         "Not Found",
    #         "Unauthorized",
    #         "Server Error"
    #     ]
    # }
    question_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Stored separately so evaluation does not depend
    # on asking the LLM again.
    correct_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Question-level difficulty.
    difficulty: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    # Used later when weighting evidence.
    discrimination: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    
class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    learner_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    assessment_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "assessments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Number of questions answered correctly.
    correct_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Total number of questions in the assessment.
    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Normalized score: 0.0 -> 1.0
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    attempt_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "assessment_attempts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "assessment_questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # What the learner submitted.
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Determined by our evaluator.
    correct: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # Normalized question-level score.
    #
    # 0.0 = incorrect
    # 1.0 = correct
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )