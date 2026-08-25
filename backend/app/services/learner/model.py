from sqlalchemy.orm import Session

from app.db.models.learner import LearnerEvidence
from app.db.models.learner import LearnerSkillState


class LearnerModelService:

    LEARNING_RATE = 0.30

    def __init__(self, db: Session):
        self.db = db

    def update_from_evidence(
        self,
        *,
        evidence: LearnerEvidence,
    ) -> LearnerSkillState:

        # -----------------------------------------
        # 1. Find existing learner skill state
        # -----------------------------------------

        state = (
            self.db.query(LearnerSkillState)
            .filter(
                LearnerSkillState.learner_id
                == evidence.learner_id,
                LearnerSkillState.skill_id
                == evidence.skill_id,
            )
            .first()
        )

        # -----------------------------------------
        # 2. Create initial state if necessary
        # -----------------------------------------

        if state is None:

            state = LearnerSkillState(
                learner_id=evidence.learner_id,
                skill_id=evidence.skill_id,
                theta=0.0,
                confidence=0.0,
                status="locked",
                attempts=0,
                mastery=0.0,
            )

            self.db.add(state)

            # Make the new row available to SQLAlchemy
            # before we continue modifying it.
            self.db.flush()

        # -----------------------------------------
        # 3. Update mastery
        # -----------------------------------------

        old_mastery = state.mastery

        state.mastery = (
            old_mastery
            + self.LEARNING_RATE
            * (evidence.score - old_mastery)
        )

        # -----------------------------------------
        # 4. Update theta
        # -----------------------------------------

        #
        # Convert mastery [0, 1] into a simple
        # ability estimate roughly centered around 0.
        #
        # mastery = 0.0 -> theta = -3
        # mastery = 0.5 -> theta =  0
        # mastery = 1.0 -> theta = +3
        #

        state.theta = (
            (state.mastery * 6.0) - 3.0
        )

        # -----------------------------------------
        # 5. Update confidence
        # -----------------------------------------

        state.attempts += 1

        state.confidence = min(
            1.0,
            state.confidence + 0.20,
        )

        # -----------------------------------------
        # 6. Determine learning status
        # -----------------------------------------

        state.status = self._determine_status(
            mastery=state.mastery,
            attempts=state.attempts,
        )

        # -----------------------------------------
        # 7. Persist
        # -----------------------------------------

        try:

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise

        self.db.refresh(state)

        return state

    @staticmethod
    def _determine_status(
        *,
        mastery: float,
        attempts: int,
    ) -> str:

        if mastery >= 0.85:
            return "mastered"

        if attempts > 0:
            return "learning"

        return "available"