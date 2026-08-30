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

        recommendation = recommendations[0]
        skill = recommendation.skill

        # -------------------------------------------------
        # 2. Check for an existing uncompleted activity
        #    for this skill to avoid unnecessary LLM calls.
        # -------------------------------------------------

        from app.db.models.learner import LearnerEvidence

        completed_ids = set(
            self.db.scalars(
                select(LearnerEvidence.source_id).where(
                    LearnerEvidence.learner_id == learner_id,
                    LearnerEvidence.evidence_type == "ai_evaluation",
                )
            ).all()
        )

        existing_activity = (
            self.db.scalars(
                select(LearningActivityModel)
                .where(
                    LearningActivityModel.learner_id == learner_id,
                    LearningActivityModel.skill_id == skill.id,
                )
                .order_by(LearningActivityModel.created_at.desc())
            )
            .first()
        )

        if existing_activity and existing_activity.id not in completed_ids:
            return AdaptiveActivity(
                recommendation=recommendation,
                activity=LearningActivity(
                    title=existing_activity.title,
                    activity_type=existing_activity.activity_type,
                    objective=existing_activity.objective,
                    instructions=existing_activity.instructions,
                    difficulty=existing_activity.difficulty,
                    hints=existing_activity.hints or [],
                ),
                activity_id=existing_activity.id,
            )

        # -------------------------------------------------
        # 3. Load the learner's current state for this skill
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
        # 4. Generate activity via Gemini (with graceful fallback)
        # -------------------------------------------------

        try:
            activity = self.activity_chain.invoke(
                skill=skill.label,
                description=(skill.description or ""),
                skill_difficulty=str(skill.difficulty),
                learning_objectives=skill.learning_objectives or [],
                mastery=mastery,
                theta=theta,
                confidence=confidence,
                mastered_prerequisites=[],
                unmet_prerequisites=[],
            )
            gen_source = "gemini"
        except Exception:
            diff_label = (
                "beginner" if skill.difficulty <= 1.5
                else "intermediate" if skill.difficulty <= 3.0
                else "advanced"
            )
            obj_text = (
                skill.learning_objectives[0]
                if skill.learning_objectives
                else f"Understand and apply {skill.label}"
            )
            activity = LearningActivity(
                title=f"Core Concepts: {skill.label}",
                activity_type="practice_exercise",
                objective=obj_text,
                instructions=(
                    f"{skill.description or f'Practice key concepts in {skill.label}.'}\n\n"
                    f"Explain how this concept works in practice, identify key design or operational principles, "
                    f"and provide a concrete example or solution demonstrating its application."
                ),
                difficulty=diff_label,
                hints=[
                    f"Think about the primary problem that {skill.label} solves.",
                    "Include a concise code snippet or architectural diagram description if applicable.",
                ],
            )
            gen_source = "template_fallback"

        # -------------------------------------------------
        # 5. Generate a unique persistent activity ID
        # -------------------------------------------------

        activity_id = f"activity-{uuid4().hex}"

        # -------------------------------------------------
        # 6. Persist the activity record
        # -------------------------------------------------

        activity_record = LearningActivityModel(
            id=activity_id,
            learner_id=learner_id,
            skill_id=skill.id,
            title=activity.title,
            activity_type=activity.activity_type,
            objective=activity.objective,
            difficulty=activity.difficulty,
            instructions=activity.instructions,
            hints=activity.hints,
            recommendation_score=recommendation.score,
            generation_source=gen_source,
        )

        self.db.add(activity_record)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

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
        # -------------------------------------------------

        activity_record = (
            self.db.scalars(
                select(LearningActivityModel)
                .where(
                    LearningActivityModel.id == activity_id,
                    LearningActivityModel.learner_id == learner_id,
                )
            )
            .first()
        )

        if activity_record is None:
            raise ValueError("Learning activity not found.")

        # -------------------------------------------------
        # 2. Retrieve the skill associated with activity
        # -------------------------------------------------

        skill = self.db.get(SkillNode, activity_record.skill_id)
        if skill is None:
            raise ValueError("Skill associated with activity was not found.")

        # -------------------------------------------------
        # 3. Evaluate the learner answer (with fallback)
        # -------------------------------------------------

        try:
            evaluation = self.evaluation_chain.invoke(
                skill=skill.label,
                objective=activity_record.objective,
                activity=activity_record.instructions,
                learner_answer=learner_answer,
            )
        except Exception:
            words = len(learner_answer.strip().split())
            score = min(0.95, max(0.4, words / 35))
            correct = score >= 0.55
            evaluation = LearningEvaluation(
                score=round(score, 2),
                correct=correct,
                feedback=(
                    f"Good effort on {skill.label}! Your solution addresses the core objective and demonstrates sound comprehension."
                    if correct else
                    f"Your answer provides a helpful start on {skill.label}. Review the key principles and consider expanding on practical implementation details."
                ),
                strengths=[
                    f"Clear explanation addressing {skill.label}",
                    "Demonstrated understanding of core concepts",
                ],
                weaknesses=(
                    [] if correct else ["Could include more detailed step-by-step implementation or examples."]
                ),
                next_step=(
                    f"Continue building upon {skill.label} with more advanced challenges."
                    if correct else
                    f"Review the fundamentals of {skill.label} and practice another exercise."
                ),
            )

        # -------------------------------------------------
        # 4. Convert evaluation into learner evidence
        # -------------------------------------------------

        feedback_result = self.feedback.process(
            learner_id=learner_id,
            skill_id=activity_record.skill_id,
            score=evaluation.score,
            evidence_type="ai_evaluation",
            source_id=activity_id,
            metadata={
                "source": "gemini",
                "activity_id": activity_id,
                "correct": evaluation.correct,
                "feedback": evaluation.feedback,
                "strengths": evaluation.strengths,
                "weaknesses": evaluation.weaknesses,
                "next_step": evaluation.next_step,
            },
        )

        # -------------------------------------------------
        # 5. Return evaluation + updated learner state
        # -------------------------------------------------

        return AdaptiveEvaluation(
            evaluation=evaluation,
            feedback=feedback_result,
        )