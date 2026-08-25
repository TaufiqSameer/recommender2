from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.learning_activity import (
    LearningActivityChain,
)

from app.ai.chains.learning_evaluation import (
    LearningEvaluationChain,
)

from app.ai.llm.schemas import (
    LearningActivity,
    LearningEvaluation,
)

from app.db.models import (
    LearnerSkillState,
    LearningActivity as LearningActivityModel,
    SkillNode,
)

from app.services.learning.feedback import (
    FeedbackResult,
    LearningFeedbackService,
)

from app.services.learning.recommender import (
    LearningRecommender,
    Recommendation,
)


# =========================================================
# RESULT OBJECTS
# =========================================================


@dataclass
class AdaptiveActivity:

    recommendation: Recommendation

    activity: LearningActivity

    activity_id: str


@dataclass
class AdaptiveEvaluation:

    evaluation: LearningEvaluation

    feedback: FeedbackResult


# =========================================================
# ADAPTIVE LEARNING SERVICE
# =========================================================


class AdaptiveLearningService:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

        self.recommender = (
            LearningRecommender(db)
        )

        self.activity_chain = (
            LearningActivityChain()
        )

        self.evaluation_chain = (
            LearningEvaluationChain()
        )

        self.feedback = (
            LearningFeedbackService(db)
        )

    # =====================================================
    # GENERATE NEXT ACTIVITY
    # =====================================================

    def generate_next_activity(
        self,
        learner_id: str,
    ) -> AdaptiveActivity | None:

        # -------------------------------------------------
        # 1. Ask the recommender for the best skill
        # -------------------------------------------------

        recommendations = (
            self.recommender.recommend(
                learner_id=learner_id,
                limit=1,
            )
        )

        if not recommendations:

            return None

        recommendation = (
            recommendations[0]
        )

        skill = recommendation.skill

        # -------------------------------------------------
        # 2. Load the learner's current state for this skill
        # -------------------------------------------------

        state = (
            self.db.scalars(
                select(
                    LearnerSkillState
                )
                .where(
                    LearnerSkillState.learner_id
                    == learner_id,

                    LearnerSkillState.skill_id
                    == skill.id,
                )
            )
            .first()
        )

        if state is None:

            mastery = 0.0
            theta = 0.0
            confidence = 0.0

        else:

            mastery = state.mastery
            theta = state.theta
            confidence = state.confidence

        # -------------------------------------------------
        # 3. Ask Gemini to generate the activity
        # -------------------------------------------------

        activity = (
            self.activity_chain.invoke(
                skill=skill.label,

                description=(
                    skill.description
                    or ""
                ),

                skill_difficulty=str(
                    skill.difficulty
                ),

                learning_objectives=(
                    skill.learning_objectives
                ),

                mastery=mastery,

                theta=theta,

                confidence=confidence,

                mastered_prerequisites=[],

                unmet_prerequisites=[],
            )
        )

        # -------------------------------------------------
        # 4. Generate a unique persistent activity ID
        # -------------------------------------------------

        activity_id = (
            f"activity-{uuid4().hex}"
        )

        # -------------------------------------------------
        # 5. Persist the exact Gemini activity
        # -------------------------------------------------

        activity_record = (
            LearningActivityModel(
                id=activity_id,

                learner_id=learner_id,

                skill_id=skill.id,

                title=activity.title,

                activity_type=(
                    activity.activity_type
                ),

                objective=activity.objective,

                difficulty=activity.difficulty,

                instructions=(
                    activity.instructions
                ),

                hints=activity.hints,

                recommendation_score=(
                    recommendation.score
                ),

                generation_source="gemini",
            )
        )

        self.db.add(
            activity_record
        )

        # -------------------------------------------------
        # 6. Persist the activity
        # -------------------------------------------------

        try:

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise

        # -------------------------------------------------
        # 7. Return activity + persistent ID
        # -------------------------------------------------

        return AdaptiveActivity(
            recommendation=recommendation,

            activity=activity,

            activity_id=activity_id,
        )

    # =====================================================
    # EVALUATE LEARNER RESPONSE
    # =====================================================

    def evaluate_response(
        self,
        *,
        learner_id: str,
        activity_id: str,
        learner_answer: str,
    ) -> AdaptiveEvaluation:

        # -------------------------------------------------
        # 1. Retrieve the exact activity
        #
        # The client only provides activity_id.
        # The backend is responsible for retrieving
        # the actual activity from the database.
        # -------------------------------------------------

        activity_record = (
            self.db.scalars(
                select(
                    LearningActivityModel
                )
                .where(
                    LearningActivityModel.id
                    == activity_id,

                    LearningActivityModel.learner_id
                    == learner_id,
                )
            )
            .first()
        )

        if activity_record is None:

            raise ValueError(
                "Learning activity not found."
            )

        # -------------------------------------------------
        # 2. Retrieve the skill associated with activity
        # -------------------------------------------------

        skill = self.db.get(
            SkillNode,
            activity_record.skill_id,
        )

        if skill is None:

            raise ValueError(
                "Skill associated with activity "
                "was not found."
            )

        # -------------------------------------------------
        # 3. Ask Gemini to evaluate the learner answer
        #
        # IMPORTANT:
        #
        # The activity information comes from our database,
        # not from the client.
        # -------------------------------------------------

        evaluation = (
            self.evaluation_chain.invoke(
                skill=skill.label,

                objective=(
                    activity_record.objective
                ),

                activity=(
                    activity_record.instructions
                ),

                learner_answer=(
                    learner_answer
                ),
            )
        )

        # -------------------------------------------------
        # 4. Convert evaluation into learner evidence
        # -------------------------------------------------

        feedback_result = (
            self.feedback.process(
                learner_id=learner_id,

                skill_id=(
                    activity_record.skill_id
                ),

                score=evaluation.score,

                evidence_type="ai_evaluation",

                source_id=(
                    f"activity-evaluation-"
                    f"{activity_id}"
                ),

                metadata={

                    "source": "gemini",

                    "activity_id": (
                        activity_id
                    ),

                    "correct": (
                        evaluation.correct
                    ),

                    "feedback": (
                        evaluation.feedback
                    ),

                    "strengths": (
                        evaluation.strengths
                    ),

                    "weaknesses": (
                        evaluation.weaknesses
                    ),

                    "next_step": (
                        evaluation.next_step
                    ),
                },
            )
        )

        # -------------------------------------------------
        # 5. Return evaluation + updated learner state
        # -------------------------------------------------

        return AdaptiveEvaluation(
            evaluation=evaluation,

            feedback=feedback_result,
        )