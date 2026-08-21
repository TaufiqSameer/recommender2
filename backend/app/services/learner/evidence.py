from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LearnerEvidence


class LearnerEvidenceService:

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        learner_id: str,
        skill_id: str,
        evidence_type: str,
        score: float,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LearnerEvidence:

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                "Evidence score must be between 0.0 and 1.0."
            )

        evidence = LearnerEvidence(
            learner_id=learner_id,
            skill_id=skill_id,
            evidence_type=evidence_type,
            source_id=source_id,
            score=score,
            evidence_metadata=metadata or {},
        )

        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)

        return evidence

    def get(
        self,
        evidence_id: int,
    ) -> LearnerEvidence | None:

        return self.db.get(
            LearnerEvidence,
            evidence_id,
        )

    def get_for_learner(
        self,
        learner_id: str,
    ) -> list[LearnerEvidence]:

        stmt = (
            select(LearnerEvidence)
            .where(
                LearnerEvidence.learner_id == learner_id
            )
            .order_by(
                LearnerEvidence.created_at.desc()
            )
        )

        return list(self.db.scalars(stmt).all())

    def get_for_skill(
        self,
        learner_id: str,
        skill_id: str,
    ) -> list[LearnerEvidence]:

        stmt = (
            select(LearnerEvidence)
            .where(
                LearnerEvidence.learner_id == learner_id,
                LearnerEvidence.skill_id == skill_id,
            )
            .order_by(
                LearnerEvidence.created_at.desc()
            )
        )

        return list(self.db.scalars(stmt).all())