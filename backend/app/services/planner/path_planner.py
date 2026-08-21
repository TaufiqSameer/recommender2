from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import LearnerSkillState, SkillNode
from app.services.goals.goal_mapper import GoalMapper
from app.services.skill_graph.traversal import SkillGraphService


@dataclass
class RecommendedSkill:
    skill_id: str
    label: str
    mastery: float
    difficulty: float
    reason: str


class LearningPathPlanner:

    def __init__(self, db: Session):
        self.db = db
        self.graph = SkillGraphService(db)
        self.goal_mapper = GoalMapper()

    def build_path(
        self,
        learner_id: str,
        target_skill_id: str,
        max_steps: int = 10,
    ) -> list[RecommendedSkill]:

        target = self.graph.get_skill(
            target_skill_id
        )

        if target is None:
            raise ValueError(
                f"Unknown target skill: {target_skill_id}"
            )

        return self._build_path_from_targets(
            learner_id=learner_id,
            target_skill_ids={target_skill_id},
            states=self._get_skill_states(learner_id),
            max_steps=max_steps,
        )

    def build_path_for_role(
        self,
        learner_id: str,
        role_id: str,
        max_steps: int = 10,
    ) -> list[RecommendedSkill]:

        required_skills = (
            self.goal_mapper.get_required_skills(
                role_id
            )
        )

        return self._build_path_from_targets(
            learner_id=learner_id,
            target_skill_ids=set(required_skills),
            states=self._get_skill_states(learner_id),
            max_steps=max_steps,
        )

    def _build_path_from_targets(
        self,
        learner_id: str,
        target_skill_ids: set[str],
        states: dict[str, LearnerSkillState],
        max_steps: int,
    ) -> list[RecommendedSkill]:

        required_ids: set[str] = set()

        for target_skill_id in target_skill_ids:

            if self.graph.get_skill(target_skill_id) is None:
                raise ValueError(
                    f"Unknown target skill: "
                    f"{target_skill_id}"
                )

            required_ids.add(target_skill_id)

            required_ids.update(
                self.graph.get_all_prerequisites(
                    target_skill_id
                )
            )

        candidates = []

        for skill_id in required_ids:

            skill = self.graph.get_skill(skill_id)

            if skill is None:
                continue

            mastery = self._mastery(
                states,
                skill_id,
            )

            if mastery >= 0.8:
                continue

            candidates.append(
                (skill, mastery)
            )

        learned = {
            skill_id
            for skill_id, state in states.items()
            if state.mastery >= 0.8
        }

        path = []

        while candidates and len(path) < max_steps:

            next_candidate = None

            for skill, mastery in candidates:

                prerequisites = (
                    self.graph.get_prerequisites(
                        skill.id
                    )
                )

                prerequisites_ready = all(
                    prerequisite.id in learned
                    or self._mastery(
                        states,
                        prerequisite.id,
                    ) >= 0.8
                    for prerequisite in prerequisites
                )

                if not prerequisites_ready:
                    continue

                gap = 1.0 - mastery

                score = (
                    gap * 0.7
                    + (
                        1.0 /
                        (1.0 + skill.difficulty)
                    ) * 0.3
                )

                if (
                    next_candidate is None
                    or score > next_candidate[0]
                ):
                    next_candidate = (
                        score,
                        skill,
                        mastery,
                    )

            if next_candidate is None:
                break

            _, skill, mastery = next_candidate

            path.append(
                RecommendedSkill(
                    skill_id=skill.id,
                    label=skill.label,
                    mastery=mastery,
                    difficulty=skill.difficulty,
                    reason=self._build_reason(
                        skill,
                        mastery,
                    ),
                )
            )

            learned.add(skill.id)

            candidates = [
                candidate
                for candidate in candidates
                if candidate[0].id != skill.id
            ]

        return path

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

    @staticmethod
    def _mastery(
        states: dict[str, LearnerSkillState],
        skill_id: str,
    ) -> float:

        state = states.get(skill_id)

        if state is None:
            return 0.0

        return state.mastery

    @staticmethod
    def _build_reason(
        skill: SkillNode,
        mastery: float,
    ) -> str:

        if mastery == 0.0:
            return (
                f"{skill.label} is a required skill "
                f"that has not been demonstrated yet."
            )

        return (
            f"{skill.label} is a prerequisite "
            f"with a current mastery of "
            f"{mastery:.0%}."
        )