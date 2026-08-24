from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.learner import LearnerEvidence
from app.db.models.learner import LearnerSkillState

from app.services.learner.evidence import (
    LearnerEvidenceService,
)

from app.services.learner.model import (
    LearnerModelService,
)


@dataclass
class FeedbackResult:
    evidence: LearnerEvidence
    state: LearnerSkillState


class LearningFeedbackService:

    def __init__(self, db: Session):

        self.db = db

        self.evidence_service = (
            LearnerEvidenceService(db)
        )

        self.learner_model = (
            LearnerModelService(db)
        )

    def process(
        self,
        *,
        learner_id: str,
        skill_id: str,
        score: float,
        evidence_type: str,
        source_id: str | None = None,
        metadata: dict | None = None,
    ) -> FeedbackResult:

        # -----------------------------------------
        # 1. Record evidence
        # -----------------------------------------

        evidence = self.evidence_service.record(
            learner_id=learner_id,
            skill_id=skill_id,
            evidence_type=evidence_type,
            score=score,
            source_id=source_id,
            metadata=metadata,
        )

        # -----------------------------------------
        # 2. Update learner model
        # -----------------------------------------

        state = (
            self.learner_model.update_from_evidence(
                evidence=evidence,
            )
        )

        # -----------------------------------------
        # 3. Return both pieces of information
        # -----------------------------------------

        return FeedbackResult(
            evidence=evidence,
            state=state,
        )