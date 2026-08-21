from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LearnerSkillState


class LearnerSkillStateService:

    def __init__(self, db: Session):
        self.db = db

    def get(
        self,
        learner_id: str,
        skill_id: str,
    ) -> LearnerSkillState | None:

        return self.db.get(
            LearnerSkillState,
            (learner_id, skill_id),
        )

    def get_for_learner(
        self,
        learner_id: str,
    ) -> list[LearnerSkillState]:

        stmt = (
            select(LearnerSkillState)
            .where(
                LearnerSkillState.learner_id == learner_id
            )
            .order_by(
                LearnerSkillState.skill_id
            )
        )

        return list(self.db.scalars(stmt).all())

    def create(
        self,
        learner_id: str,
        skill_id: str,
    ) -> LearnerSkillState:

        existing = self.get(
            learner_id,
            skill_id,
        )

        if existing is not None:
            raise ValueError(
                f"Skill state already exists for "
                f"'{learner_id}' → '{skill_id}'."
            )

        state = LearnerSkillState(
            learner_id=learner_id,
            skill_id=skill_id,
            theta=0.0,
            confidence=0.0,
            mastery=0.0,
            status="unknown",
            attempts=0,
        )

        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)

        return state

    def update(
        self,
        learner_id: str,
        skill_id: str,
        *,
        theta: float | None = None,
        confidence: float | None = None,
        mastery: float | None = None,
        status: str | None = None,
    ) -> LearnerSkillState:

        state = self.get(
            learner_id,
            skill_id,
        )

        if state is None:
            raise ValueError(
                f"No skill state exists for "
                f"'{learner_id}' → '{skill_id}'."
            )

        if theta is not None:
            state.theta = theta

        if confidence is not None:
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(
                    "Confidence must be between 0.0 and 1.0."
                )

            state.confidence = confidence

        if mastery is not None:
            if not 0.0 <= mastery <= 1.0:
                raise ValueError(
                    "Mastery must be between 0.0 and 1.0."
                )

            state.mastery = mastery

        if status is not None:
            state.status = status

        state.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(state)

        return state