from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    LearnerSkillState,
    SkillEdge,
    SkillNode,
)



@dataclass
class LearningCandidate:
    skill: SkillNode
    mastery: float | None
    prerequisites_satisfied: bool
    prerequisite_count: int
    prerequisite_ids: list[str]
    unlocked_skill_count: int


@dataclass
class SkillEligibility:
    """
    Describes whether a skill is currently available
    and, if not, which prerequisites are blocking it.
    """

    skill: SkillNode
    eligible: bool
    mastery: float | None

    prerequisites: list[str]
    satisfied_prerequisites: list[str]
    unsatisfied_prerequisites: list[str]


class CandidateSelector:

    # A prerequisite is considered satisfied once
    # the learner reaches this mastery level.
    PREREQUISITE_MASTERY_THRESHOLD = 0.70

    # A skill above this level is considered mastered.
    MASTERY_THRESHOLD = 0.85

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # LOAD CURRENT LEARNER STATE
    # =========================================================

    def _get_states(
        self,
        learner_id: str,
    ) -> dict[str, LearnerSkillState]:

        return {
            state.skill_id: state
            for state in self.db.scalars(
                select(LearnerSkillState)
                .where(
                    LearnerSkillState.learner_id
                    == learner_id
                )
            ).all()
        }

    # =========================================================
    # LOAD SKILL GRAPH
    # =========================================================

    def _get_graph(
        self,
    ) -> tuple[
        list[SkillNode],
        dict[str, list[str]],
        dict[str, list[str]],
    ]:

        skills = list(
            self.db.scalars(
                select(SkillNode)
            ).all()
        )

        edges = list(
            self.db.scalars(
                select(SkillEdge)
            ).all()
        )

        # -----------------------------------------------------
        # prerequisite map
        #
        # rest -> [http]
        # authentication -> [http, json]
        # -----------------------------------------------------

        prerequisites_by_skill: dict[
            str,
            list[str],
        ] = defaultdict(list)

        # -----------------------------------------------------
        # dependent map
        #
        # http -> [rest, authentication]
        # -----------------------------------------------------

        dependents_by_skill: dict[
            str,
            list[str],
        ] = defaultdict(list)

        for edge in edges:

            prerequisites_by_skill[
                edge.dependent_id
            ].append(
                edge.prerequisite_id
            )

            dependents_by_skill[
                edge.prerequisite_id
            ].append(
                edge.dependent_id
            )

        return (
            skills,
            prerequisites_by_skill,
            dependents_by_skill,
        )

    # =========================================================
    # CHECK ONE SKILL
    # =========================================================

    def _evaluate_skill(
        self,
        *,
        skill: SkillNode,
        states: dict[str, LearnerSkillState],
        prerequisites_by_skill: dict[str, list[str]],
    ) -> SkillEligibility:

        state = states.get(skill.id)

        mastery = (
            state.mastery
            if state is not None
            else None
        )

        prerequisites = (
            prerequisites_by_skill.get(
                skill.id,
                [],
            )
        )

        satisfied_prerequisites = []
        unsatisfied_prerequisites = []

        # -----------------------------------------------------
        # Check every prerequisite.
        #
        # This is STRICT AND logic:
        #
        # HTTP >= 0.70
        # AND
        # JSON >= 0.70
        # -----------------------------------------------------

        for prerequisite_id in prerequisites:

            prerequisite_state = states.get(
                prerequisite_id
            )

            if (
                prerequisite_state is not None
                and prerequisite_state.mastery
                >= self.PREREQUISITE_MASTERY_THRESHOLD
            ):

                satisfied_prerequisites.append(
                    prerequisite_id
                )

            else:

                unsatisfied_prerequisites.append(
                    prerequisite_id
                )

        prerequisites_satisfied = (
            len(unsatisfied_prerequisites) == 0
        )

        # -----------------------------------------------------
        # Determine whether the skill itself is already
        # mastered.
        # -----------------------------------------------------

        already_mastered = False

        if state is not None:

            if state.status == "mastered":
                already_mastered = True

            elif state.mastery >= self.MASTERY_THRESHOLD:
                already_mastered = True

        eligible = (
            not already_mastered
            and prerequisites_satisfied
        )

        return SkillEligibility(
            skill=skill,
            eligible=eligible,
            mastery=mastery,
            prerequisites=list(prerequisites),
            satisfied_prerequisites=(
                satisfied_prerequisites
            ),
            unsatisfied_prerequisites=(
                unsatisfied_prerequisites
            ),
        )

    # =========================================================
    # GET ELIGIBLE CANDIDATES
    # =========================================================

    def get_candidates(
        self,
        learner_id: str,
    ) -> list[LearningCandidate]:

        states = self._get_states(
            learner_id
        )

        (
            skills,
            prerequisites_by_skill,
            dependents_by_skill,
        ) = self._get_graph()

        candidates = []

        for skill in skills:

            eligibility = self._evaluate_skill(
                skill=skill,
                states=states,
                prerequisites_by_skill=(
                    prerequisites_by_skill
                ),
            )

            # -------------------------------------------------
            # CandidateSelector only returns skills that
            # are actually available to learn.
            # -------------------------------------------------

            if not eligibility.eligible:
                continue

            unlocked_skill_count = 0

            for dependent_id in (
                dependents_by_skill.get(
                    skill.id,
                    [],
                )
            ):

                dependent_state = states.get(
                    dependent_id
                )

                if (
                    dependent_state is None
                    or dependent_state.mastery
                    < self.MASTERY_THRESHOLD
                ):

                    unlocked_skill_count += 1

            candidates.append(
                LearningCandidate(
                    skill=skill,
                    mastery=eligibility.mastery,
                    prerequisites_satisfied=True,
                    prerequisite_count=len(
                        eligibility.prerequisites
                    ),
                    prerequisite_ids=list(eligibility.prerequisites),
                    unlocked_skill_count=(
                        unlocked_skill_count
                    ),
                )
            )

        return candidates

    # =========================================================
    # GET STATUS OF EVERY SKILL
    # =========================================================

    def get_skill_status(
        self,
        learner_id: str,
    ) -> list[SkillEligibility]:

        states = self._get_states(
            learner_id
        )

        (
            skills,
            prerequisites_by_skill,
            _,
        ) = self._get_graph()

        statuses = []

        for skill in skills:

            status = self._evaluate_skill(
                skill=skill,
                states=states,
                prerequisites_by_skill=(
                    prerequisites_by_skill
                ),
            )

            statuses.append(status)

        return statuses