from __future__ import annotations

from typing import Any

from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SkillNode(Base):
    __tablename__ = "skill_nodes"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    domain: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    label: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    difficulty: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    learning_objectives: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )


class SkillEdge(Base):
    __tablename__ = "skill_edges"

    prerequisite_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("skill_nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    dependent_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("skill_nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )