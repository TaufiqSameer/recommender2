from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    LearnerSkillState,
    SkillNode,
)

from app.services.learning.candidate_selector import (
    CandidateSelector,
    LearningCandidate,
)

@dataclass
class ScoreBreakdown:
    level_fit: float
    mastery_gap: float
    prerequisite_readiness: float
    unlock_value: float
    exploration: float
    final_score: float


@dataclass
class Recommendation:
    skill: SkillNode
    score: float
    reason: str
    breakdown: ScoreBreakdown


class LearningRecommender:

    # =========================================================
    # SCORE WEIGHTS
    # =========================================================
    #
    # The recommendation score is composed of:
    #
    #   30% -> learner / skill level fit
    #   25% -> mastery opportunity
    #   20% -> prerequisite readiness
    #   20% -> graph unlock value
    #    5% -> exploration / uncertainty
    #
    # All factors are normalized to [0, 1].
    #

    LEVEL_WEIGHT = 0.30
    MASTERY_GAP_WEIGHT = 0.25
    PREREQUISITE_WEIGHT = 0.20
    UNLOCK_WEIGHT = 0.15
    EXPLORATION_WEIGHT = 0.10

    # Target mastery for a skill that is currently being learned.
    TARGET_MASTERY = 0.70

    # ---------------------------------------------------------
    # Difficulty normalization
    # ---------------------------------------------------------

    DIFFICULTY_MAP = {
        "beginner": 0.25,
        "easy": 0.25,

        "intermediate": 0.50,
        "medium": 0.50,

        "advanced": 0.75,
        "hard": 0.75,

        "expert": 1.00,
    }

    def __init__(self, db: Session):

        self.db = db

        self.selector = CandidateSelector(
            db
        )

    # =========================================================
    # PUBLIC API
    # =========================================================

    def recommend(
        self,
        *,
        learner_id: str,
        limit: int = 5,
    ) -> list[Recommendation]:

        # -----------------------------------------------------
        # 1. Get CURRENT eligible candidates
        # -----------------------------------------------------

        candidates = self.selector.get_candidates(
            learner_id
        )

        if not candidates:

            return []

        # -----------------------------------------------------
        # 2. Load CURRENT learner states
        #
        # This is deliberately performed every time.
        #
        # Feedback can modify the learner model immediately
        # before recommend() is called.
        # -----------------------------------------------------

        states = {
            state.skill_id: state
            for state in self.db.scalars(
                select(LearnerSkillState)
                .where(
                    LearnerSkillState.learner_id
                    == learner_id
                )
            ).all()
        }

        # -----------------------------------------------------
        # 3. Calculate learner's current ability
        # -----------------------------------------------------

        learner_ability = (
            self._calculate_learner_ability(
                states
            )
        )

        # -----------------------------------------------------
        # 4. Find maximum graph unlock value
        # -----------------------------------------------------

        max_unlocks = max(
            (
                candidate.unlocked_skill_count
                for candidate in candidates
            ),
            default=0,
        )

        # -----------------------------------------------------
        # 5. Score every candidate
        # -----------------------------------------------------

        recommendations = []

        for candidate in candidates:

            skill = candidate.skill

            state = states.get(
                skill.id
            )

            # =================================================
            # A. LEARNER / LEVEL FIT
            # =================================================

            level_fit = (
                self._calculate_level_fit(
                    candidate=candidate,
                    learner_ability=learner_ability,
                    learner_states=states,
                )
            )

            # =================================================
            # B. MASTERY OPPORTUNITY
            # =================================================

            mastery_gap = (
                self._calculate_mastery_gap(
                    state
                )
            )

            # =================================================
            # C. PREREQUISITE READINESS
            # =================================================

            prerequisite_readiness = (
                self._calculate_prerequisite_readiness(
                    candidate=candidate,
                    learner_states=states,
                )
            )

            # =================================================
            # D. UNLOCK VALUE
            # =================================================

            unlock_value = (
                self._calculate_unlock_value(
                    candidate=candidate,
                    max_unlocks=max_unlocks,
                )
            )

            # =================================================
            # E. EXPLORATION / UNCERTAINTY
            # =================================================

            exploration_value = (
                self._calculate_exploration_value(
                    state
                )
            )

            # =================================================
            # F. FINAL SCORE
            # =================================================

            score = (

                self.LEVEL_WEIGHT
                * level_fit

                +

                self.MASTERY_GAP_WEIGHT
                * mastery_gap

                +

                self.PREREQUISITE_WEIGHT
                * prerequisite_readiness

                +

                self.UNLOCK_WEIGHT
                * unlock_value

                +

                self.EXPLORATION_WEIGHT
                * exploration_value
            )

            # -------------------------------------------------
            # Clamp score to [0, 1]
            # -------------------------------------------------

            score = max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            )

            # =================================================
            # G. EXPLANATION
            # =================================================

            reason = self._build_reason(
                candidate=candidate,
                state=state,
                level_fit=level_fit,
                mastery_gap=mastery_gap,
                prerequisite_readiness=(
                    prerequisite_readiness
                ),
                unlock_value=unlock_value,
                exploration_value=(
                    exploration_value
                ),
            )

            breakdown = ScoreBreakdown(
                level_fit=level_fit,
                mastery_gap=mastery_gap,
                prerequisite_readiness=prerequisite_readiness,
                unlock_value=unlock_value,
                exploration=exploration_value,
                final_score=score,
            )

            recommendations.append(
                Recommendation(
                    skill=skill,
                    score=score,
                    reason=reason,
                    breakdown=breakdown,
                )
            )

        # -----------------------------------------------------
        # 6. Highest score first
        # -----------------------------------------------------

        recommendations.sort(
            key=lambda recommendation:
                recommendation.score,
            reverse=True,
        )

        # -----------------------------------------------------
        # 7. Return top N
        # -----------------------------------------------------

        return recommendations[:limit]

    # =========================================================
    # LEARNER ABILITY
    # =========================================================

    @staticmethod
    def _calculate_learner_ability(
        states: dict[
            str,
            LearnerSkillState,
        ],
    ) -> float:

        if not states:

            # No evidence means we have no strong estimate
            # of learner ability.
            #
            # Use the neutral midpoint.

            return 0.50

        masteries = [
            max(
                0.0,
                min(
                    1.0,
                    state.mastery,
                ),
            )
            for state in states.values()
        ]

        if not masteries:

            return 0.50

        # -----------------------------------------------------
        # For now, use the average observed mastery.
        #
        # This is our baseline learner ability model.
        #
        # Later we can replace this with a more principled
        # theta-based ability estimator.
        # -----------------------------------------------------

        return (
            sum(masteries)
            / len(masteries)
        )

    # =========================================================
    # LEVEL FIT
    # =========================================================

    def _calculate_level_fit(
        self,
        *,
        candidate: LearningCandidate,
        learner_ability: float,
        learner_states: dict[
            str,
            LearnerSkillState,
        ],
    ) -> float:

        skill = candidate.skill

        state = learner_states.get(
            skill.id
        )

        # -----------------------------------------------------
        # If the learner already has evidence for this skill,
        # measure how close the skill is to the learning zone.
        # -----------------------------------------------------

        if state is not None:

            mastery = max(
                0.0,
                min(
                    1.0,
                    state.mastery,
                ),
            )

            # Around 0.50 is considered a useful learning zone.
            #
            # Too close to 0:
            #     learner may lack prerequisites / foundation.
            #
            # Too close to 1:
            #     learner is already nearly done.

            distance = abs(
                mastery - 0.50
            )

            return max(
                0.0,
                1.0 - (
                    distance * 2.0
                ),
            )

        # -----------------------------------------------------
        # No evidence:
        #
        # Compare candidate difficulty against estimated
        # learner ability.
        # -----------------------------------------------------

        difficulty = (
            self._difficulty_value(
                skill.difficulty
            )
        )

        distance = abs(
            learner_ability
            - difficulty
        )

        return max(
            0.0,
            1.0 - distance,
        )

    # =========================================================
    # MASTERY GAP
    # =========================================================

    def _calculate_mastery_gap(
        self,
        state: LearnerSkillState | None,
    ) -> float:

        # -----------------------------------------------------
        # No evidence:
        #
        # The learner has a large opportunity to learn this
        # skill.
        # -----------------------------------------------------

        if state is None:

            return 1.0

        mastery = max(
            0.0,
            min(
                1.0,
                state.mastery,
            ),
        )

        gap = (
            self.TARGET_MASTERY
            - mastery
        )

        return max(
            0.0,
            min(
                1.0,
                gap / self.TARGET_MASTERY,
            ),
        )

    # =========================================================
    # PREREQUISITE READINESS
    # =========================================================

    @staticmethod
    def _calculate_prerequisite_readiness(
        *,
        candidate: LearningCandidate,
        learner_states: dict[
            str,
            LearnerSkillState,
        ],
    ) -> float:

        # -----------------------------------------------------
        # No prerequisites
        # -----------------------------------------------------

        if not candidate.prerequisite_ids:

            # No prerequisite means the candidate is freely
            # available from the graph perspective.
            #
            # 0.50 keeps prerequisite readiness neutral rather
            # than artificially rewarding prerequisite-free
            # skills.
            #

            return 0.50

        prerequisite_masteries = []

        for prerequisite_id in (
            candidate.prerequisite_ids
        ):

            state = learner_states.get(
                prerequisite_id
            )

            if state is None:

                # CandidateSelector should normally prevent
                # this situation.

                return 0.0

            mastery = max(
                0.0,
                min(
                    1.0,
                    state.mastery,
                ),
            )

            prerequisite_masteries.append(
                mastery
            )

        # -----------------------------------------------------
        # STRICT AND semantics
        #
        # The weakest prerequisite determines readiness.
        # -----------------------------------------------------

        return min(
            prerequisite_masteries
        )

    # =========================================================
    # UNLOCK VALUE
    # =========================================================

    @staticmethod
    def _calculate_unlock_value(
        *,
        candidate: LearningCandidate,
        max_unlocks: int,
    ) -> float:

        if max_unlocks <= 0:

            return 0.0

        return max(
            0.0,
            min(
                1.0,
                candidate.unlocked_skill_count
                / max_unlocks,
            ),
        )

    # =========================================================
    # EXPLORATION / UNCERTAINTY
    # =========================================================

    @staticmethod
    def _calculate_exploration_value(
        state: LearnerSkillState | None,
    ) -> float:

        # -----------------------------------------------------
        # No evidence:
        #
        # We know very little about this skill.
        #
        # Therefore it has high information value.
        # -----------------------------------------------------

        if state is None:

            return 1.0

        confidence = max(
            0.0,
            min(
                1.0,
                state.confidence,
            ),
        )

        # -----------------------------------------------------
        # Low confidence = high uncertainty = more exploration.
        # -----------------------------------------------------

        return 1.0 - confidence

    # =========================================================
    # DIFFICULTY
    # =========================================================

    def _difficulty_value(
        self,
        difficulty,
    ) -> float:

        if difficulty is None:

            return 0.50

        value = getattr(
            difficulty,
            "value",
            difficulty,
        )

        value = str(
            value
        ).lower()

        return self.DIFFICULTY_MAP.get(
            value,
            0.50,
        )

    # =========================================================
    # EXPLANATION
    # =========================================================

    def _build_reason(
        self,
        *,
        candidate: LearningCandidate,
        state: LearnerSkillState | None,
        level_fit: float,
        mastery_gap: float,
        prerequisite_readiness: float,
        unlock_value: float,
        exploration_value: float,
    ) -> str:

        reasons = []

        # -----------------------------------------------------
        # Current evidence
        # -----------------------------------------------------

        if state is None:

            reasons.append(
                "you have no prior evidence for this skill"
            )

        else:

            reasons.append(
                f"your current mastery is "
                f"{state.mastery:.2f}"
            )

        # -----------------------------------------------------
        # Level fit
        # -----------------------------------------------------

        if level_fit >= 0.75:

            reasons.append(
                "it is well matched to your current level"
            )

        elif level_fit >= 0.50:

            reasons.append(
                "it is reasonably aligned with your current level"
            )

        else:

            reasons.append(
                "its difficulty differs from your current level"
            )

        # -----------------------------------------------------
        # Prerequisite readiness
        # -----------------------------------------------------

        if candidate.prerequisite_count > 0:

            if prerequisite_readiness >= 0.90:

                reasons.append(
                    "its prerequisites are strongly mastered"
                )

            elif prerequisite_readiness >= 0.70:

                reasons.append(
                    "its prerequisites are sufficiently mastered"
                )

            else:

                reasons.append(
                    "its prerequisites are only partially prepared"
                )

        # -----------------------------------------------------
        # Mastery opportunity
        # -----------------------------------------------------

        if mastery_gap >= 0.70:

            reasons.append(
                "there is substantial room to improve"
            )

        elif mastery_gap >= 0.30:

            reasons.append(
                "there is still meaningful room to improve"
            )

        # -----------------------------------------------------
        # Unlock value
        # -----------------------------------------------------

        if (
            candidate.unlocked_skill_count > 0
            and unlock_value >= 0.50
        ):

            reasons.append(
                f"mastering it can unlock "
                f"{candidate.unlocked_skill_count} "
                f"further skill"
                + (
                    "s"
                    if candidate.unlocked_skill_count != 1
                    else ""
                )
            )

        elif candidate.unlocked_skill_count > 0:

            reasons.append(
                "mastering it can contribute "
                "to further learning"
            )

        # -----------------------------------------------------
        # Exploration
        # -----------------------------------------------------

        if exploration_value >= 0.80:

            reasons.append(
                "there is significant uncertainty "
                "about your current ability"
            )

        elif exploration_value >= 0.40:

            reasons.append(
                "there is still some uncertainty "
                "about your current ability"
            )

        # -----------------------------------------------------
        # Final explanation
        # -----------------------------------------------------

        if not reasons:

            return (
                "This skill is currently available "
                "for learning."
            )

        result = (
            reasons[0].capitalize()
        )

        if len(reasons) > 1:

            result += ", "

            result += ", ".join(
                reasons[1:]
            )

        return result + "."