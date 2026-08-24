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
class Recommendation:
    skill: SkillNode
    score: float
    reason: str


class LearningRecommender:

    # =========================================================
    # SCORE WEIGHTS
    # =========================================================
    #
    # Final score:
    #
    #   40% -> level fit
    #   30% -> mastery gap
    #   20% -> unlock value
    #   10% -> confidence/readiness
    #
    # These weights are intentionally simple.
    # Later we can tune them or replace the scoring
    # function with a learned ranking model.
    #

    LEVEL_WEIGHT = 0.40
    MASTERY_GAP_WEIGHT = 0.30
    UNLOCK_WEIGHT = 0.20
    CONFIDENCE_WEIGHT = 0.10

    # =========================================================
    # MASTERY TARGET
    # =========================================================

    TARGET_MASTERY = 0.70

    # =========================================================
    # DIFFICULTY MAP
    # =========================================================

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
        # 1. Get CURRENT candidates
        # -----------------------------------------------------
        #
        # CandidateSelector reloads the learner state and
        # skill graph every time.
        #
        # Therefore:
        #
        # assessment
        #     ↓
        # learner state changes
        #     ↓
        # recommend()
        #     ↓
        # fresh candidates
        #
        # No cached candidate list is used here.
        #

        candidates = self.selector.get_candidates(
            learner_id
        )

        if not candidates:
            return []

        # -----------------------------------------------------
        # 2. Load CURRENT learner states
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
        # 3. Calculate learner ability
        # -----------------------------------------------------
        #
        # We use the learner's known skill mastery as a
        # simple estimate of their current ability.
        #

        learner_ability = (
            self._calculate_learner_ability(
                states
            )
        )

        # -----------------------------------------------------
        # 4. Find maximum unlock value
        # -----------------------------------------------------
        #
        # Used to normalize unlocked_skill_count into [0, 1].
        #

        max_unlocks = max(
            (
                candidate.unlocked_skill_count
                for candidate in candidates
            ),
            default=0,
        )

        # -----------------------------------------------------
        # 5. Build recommendations
        # -----------------------------------------------------

        recommendations: list[
            Recommendation
        ] = []

        for candidate in candidates:

            skill = candidate.skill

            state = states.get(
                skill.id
            )

            # =================================================
            # A. LEVEL FIT
            # =================================================

            level_fit = (
                self._calculate_level_fit(
                    candidate=candidate,
                    learner_ability=learner_ability,
                    learner_states=states,
                )
            )

            # =================================================
            # B. MASTERY GAP
            # =================================================
            #
            # A learner with low mastery has more to gain
            # from learning the skill.
            #
            # Example:
            #
            # mastery = 0.10
            # gap     = 0.90
            #
            # mastery = 0.65
            # gap     = 0.35
            #
            # No evidence means the learner has a full
            # learning opportunity.
            #

            mastery_gap = (
                self._calculate_mastery_gap(
                    state
                )
            )

            # =================================================
            # C. UNLOCK VALUE
            # =================================================

            if max_unlocks == 0:

                unlock_value = 0.0

            else:

                unlock_value = (
                    candidate.unlocked_skill_count
                    / max_unlocks
                )

            # =================================================
            # D. CONFIDENCE / READINESS
            # =================================================

            confidence_value = (
                self._calculate_confidence_value(
                    state
                )
            )

            # =================================================
            # E. FINAL SCORE
            # =================================================

            score = (

                self.LEVEL_WEIGHT
                * level_fit

                +

                self.MASTERY_GAP_WEIGHT
                * mastery_gap

                +

                self.UNLOCK_WEIGHT
                * unlock_value

                +

                self.CONFIDENCE_WEIGHT
                * confidence_value
            )

            # -------------------------------------------------
            # Keep score inside [0, 1]
            # -------------------------------------------------

            score = max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            )

            # =================================================
            # F. EXPLANATION
            # =================================================

            reason = self._build_reason(
                candidate=candidate,
                state=state,
                level_fit=level_fit,
                mastery_gap=mastery_gap,
                unlock_value=unlock_value,
                confidence_value=confidence_value,
            )

            recommendations.append(
                Recommendation(
                    skill=skill,
                    score=score,
                    reason=reason,
                )
            )

        # =====================================================
        # 6. Sort highest score first
        # =====================================================

        recommendations.sort(
            key=lambda recommendation:
                recommendation.score,
            reverse=True,
        )

        # =====================================================
        # 7. Return requested number
        # =====================================================

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

            # No learner history.
            #
            # Start at the middle of the ability scale.

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

        # -----------------------------------------------------
        # If the learner already has evidence for the skill,
        # use that mastery as a direct signal.
        # -----------------------------------------------------

        state = learner_states.get(
            skill.id
        )

        if state is not None:

            mastery = max(
                0.0,
                min(
                    1.0,
                    state.mastery,
                ),
            )

            # We want candidates that are still learnable,
            # but not completely unfamiliar.
            #
            # Around 0.50 is considered a good learning zone.

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
        # No evidence for this skill.
        #
        # Compare learner ability against skill difficulty.
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

        # No evidence means the learner has not started
        # learning this skill yet.

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
    # CONFIDENCE
    # =========================================================

    @staticmethod
    def _calculate_confidence_value(
        state: LearnerSkillState | None,
    ) -> float:

        # No evidence means we don't know much about the
        # learner yet.
        #
        # Give it a neutral value instead of automatically
        # rewarding or penalizing it.

        if state is None:

            return 0.50

        return max(
            0.0,
            min(
                1.0,
                state.confidence,
            ),
        )

    # =========================================================
    # DIFFICULTY
    # =========================================================

    def _difficulty_value(
        self,
        difficulty,
    ) -> float:

        if difficulty is None:

            return 0.50

        # Handle enum-like values.

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
        unlock_value: float,
        confidence_value: float,
    ) -> str:

        reasons = []

        # -----------------------------------------------------
        # Evidence / mastery
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
                "its difficulty is somewhat different "
                "from your current level"
            )

        # -----------------------------------------------------
        # Mastery gap
        # -----------------------------------------------------

        if mastery_gap >= 0.70:

            reasons.append(
                "there is substantial room to improve"
            )

        elif mastery_gap >= 0.30:

            reasons.append(
                "there is still meaningful room to improve"
            )

        else:

            reasons.append(
                "you are already relatively close "
                "to the mastery target"
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
        # Combine explanation
        # -----------------------------------------------------

        if not reasons:

            return (
                "This skill is currently available "
                "for learning."
            )

        if len(reasons) == 1:

            return (
                reasons[0].capitalize()
                + "."
            )

        reason = (
            reasons[0].capitalize()
        )

        reason += ", "

        reason += ", ".join(
            reasons[1:]
        )

        return (
            reason
            + "."
        )