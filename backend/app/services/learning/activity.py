from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.learning_activity import (
    LearningActivityChain,
)

from app.db.models import (
    LearnerSkillState,
    SkillNode,
)

from app.services.learning.candidate_selector import (
    CandidateSelector,
)

from app.services.learning.recommender import (
    LearningRecommender,
)


class LearningActivityService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.recommender = (
            LearningRecommender(db)
        )

        self.selector = (
            CandidateSelector(db)
        )

        self.activity_chain = (
            LearningActivityChain()
        )

    def generate_next_activity(
        self,
        learner_id: str,
    ):

        # =====================================================
        # 1. Ask the adaptive recommender what the learner
        #    should learn next.
        # =====================================================

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

        # =====================================================
        # 2. Load the CURRENT learner state.
        #
        # Do not use stale state from somewhere else.
        # =====================================================

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

        # =====================================================
        # 3. Find the candidate selected by the recommender.
        #
        # This gives us the prerequisite IDs determined by
        # the skill graph.
        # =====================================================

        candidates = (
            self.selector.get_candidates(
                learner_id
            )
        )

        candidate = next(
            (
                item
                for item in candidates
                if item.skill.id == skill.id
            ),
            None,
        )

        if candidate is None:

            raise RuntimeError(
                "Recommended skill is no longer "
                "an eligible candidate."
            )

        # =====================================================
        # 4. Load prerequisite SkillNodes.
        #
        # Gemini should receive human-readable skill names,
        # not only database IDs.
        # =====================================================

        prerequisite_ids = (
            candidate.prerequisite_ids
        )

        prerequisite_skills = []

        if prerequisite_ids:

            prerequisite_skills = list(
                self.db.scalars(
                    select(SkillNode)
                    .where(
                        SkillNode.id.in_(
                            prerequisite_ids
                        )
                    )
                ).all()
            )

        skill_by_id = {
            prerequisite.id: prerequisite
            for prerequisite
            in prerequisite_skills
        }

        # =====================================================
        # 5. Determine prerequisite status.
        # =====================================================

        mastered_prerequisites = []
        unmet_prerequisites = []

        for prerequisite_id in (
            prerequisite_ids
        ):

            prerequisite_skill = (
                skill_by_id.get(
                    prerequisite_id
                )
            )

            prerequisite_state = (
                self.db.scalars(
                    select(
                        LearnerSkillState
                    )
                    .where(
                        LearnerSkillState.learner_id
                        == learner_id,
                        LearnerSkillState.skill_id
                        == prerequisite_id,
                    )
                )
                .first()
            )

            if prerequisite_state is not None:

                if (
                    prerequisite_state.mastery
                    >= self.selector.PREREQUISITE_MASTERY_THRESHOLD
                ):

                    mastered_prerequisites.append(
                        (
                            prerequisite_skill.label
                            if prerequisite_skill
                            else prerequisite_id
                        )
                    )

                    continue

            unmet_prerequisites.append(
                (
                    prerequisite_skill.label
                    if prerequisite_skill
                    else prerequisite_id
                )
            )

        # =====================================================
        # 6. Ask Gemini to create the activity.
        # =====================================================

        activity = (
            self.activity_chain.invoke(
                skill=skill.label,
                description=skill.description,
                skill_difficulty=str(
                    skill.difficulty
                ),
                learning_objectives=(
                    skill.learning_objectives
                ),
                mastery=mastery,
                theta=theta,
                confidence=confidence,
                mastered_prerequisites=(
                    mastered_prerequisites
                ),
                unmet_prerequisites=(
                    unmet_prerequisites
                ),
            )
        )

        # =====================================================
        # 7. Return both the recommendation and activity.
        #
        # This lets the application know WHY the activity
        # was selected as well as WHAT Gemini generated.
        # =====================================================

        return {
            "recommendation": recommendation,
            "activity": activity,
        }