from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LearnerProfile


class LearnerProfileService:

    def __init__(self, db: Session):
        self.db = db

    def get(
        self,
        learner_id: str,
    ) -> LearnerProfile | None:
        return self.db.get(
            LearnerProfile,
            learner_id,
        )

    def create(
        self,
        learner_id: str,
        goal: str | None = None,
        target_role: str | None = None,
        domain: str | None = None,
        weekly_hours: float | None = None,
        learning_preferences: list[str] | None = None,
        preferences: dict | None = None,
    ) -> LearnerProfile:

        existing = self.get(learner_id)

        if existing is not None:
            raise ValueError(
                f"Learner '{learner_id}' already exists."
            )

        learner = LearnerProfile(
            learner_id=learner_id,
            goal=goal,
            target_role=target_role,
            domain=domain,
            weekly_hours=weekly_hours,
            learning_preferences=(
                learning_preferences
                if learning_preferences is not None
                else []
            ),
            preferences=(
                preferences
                if preferences is not None
                else {}
            ),
        )

        self.db.add(learner)
        self.db.commit()
        self.db.refresh(learner)

        return learner

    def update(
        self,
        learner_id: str,
        **updates,
    ) -> LearnerProfile:

        learner = self.get(learner_id)

        if learner is None:
            raise ValueError(
                f"Learner '{learner_id}' does not exist."
            )

        for field, value in updates.items():
            if hasattr(learner, field):
                setattr(learner, field, value)

        self.db.commit()
        self.db.refresh(learner)

        return learner