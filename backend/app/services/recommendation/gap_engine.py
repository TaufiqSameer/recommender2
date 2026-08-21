from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import LearnerSkillState
from app.services.skill_graph.traversal import SkillGraphService


@dataclass
class SkillGap:
    skill_id: str
    label: str
    mastery: float
    gap: float
    difficulty: float
    prerequisites: list[str]
    blocked: bool
    blocked_by: list[str]


class SkillGapEngine:

    MASTERY_THRESHOLD = 0.8

    def __init__(self, db: Session):
        self.db = db
        self.graph = SkillGraphService(db)

    def analyze(
        self,
        learner_id: str,
        target_skill_ids: set[str],
    ) -> list[SkillGap]:

        states = self._get_skill_states(
            learner_id
        )

        required_skill_ids: set[str] = set()

        for target_id in target_skill_ids:

            skill = self.graph.get_skill(target_id)

            if skill is None:
                raise ValueError(
                    f"Unknown target skill: {target_id}"
                )

            required_skill_ids.add(target_id)

            required_skill_ids.update(
                self.graph.get_all_prerequisites(
                    target_id
                )
            )

        gaps: list[SkillGap] = []

        for skill_id in required_skill_ids:

            skill = self.graph.get_skill(skill_id)

            if skill is None:
                continue

            state = states.get(skill_id)

            mastery = (
                state.mastery
                if state is not None
                else 0.0
            )

            if mastery >= self.MASTERY_THRESHOLD:
                continue

            gap = 1.0 - mastery

            prerequisites = (
                self.graph.get_prerequisites(
                    skill_id
                )
            )

            blocked_by = []

            for prerequisite in prerequisites:

                prerequisite_state = states.get(
                    prerequisite.id
                )

                prerequisite_mastery = (
                    prerequisite_state.mastery
                    if prerequisite_state is not None
                    else 0.0
                )

                if (
                    prerequisite_mastery
                    < self.MASTERY_THRESHOLD
                ):
                    blocked_by.append(
                        prerequisite.id
                    )

            gaps.append(
                SkillGap(
                    skill_id=skill.id,
                    label=skill.label,
                    mastery=mastery,
                    gap=gap,
                    difficulty=skill.difficulty,
                    prerequisites=[
                        prerequisite.id
                        for prerequisite
                        in prerequisites
                    ],
                    blocked=len(blocked_by) > 0,
                    blocked_by=blocked_by,
                )
            )

        return gaps

    def _get_skill_states(
        self,
        learner_id: str,
    ) -> dict[str, LearnerSkillState]:

        states = (
            self.db.query(LearnerSkillState)
            .filter(
                LearnerSkillState.learner_id
                == learner_id
            )
            .all()
        )

        return {
            state.skill_id: state
            for state in states
        }