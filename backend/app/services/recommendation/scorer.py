from dataclasses import dataclass

from app.services.recommendation.gap_engine import SkillGap


@dataclass
class ScoredSkill:
    skill_id: str
    label: str
    priority: float
    mastery: float
    gap: float
    difficulty: float
    blocked: bool
    blocked_by: list[str]
    reason: str


class SkillScorer:

    def score(
        self,
        gaps: list[SkillGap],
    ) -> list[ScoredSkill]:

        scored: list[ScoredSkill] = []

        for gap in gaps:

            if gap.blocked:
                continue

            priority = self._calculate_priority(gap)

            scored.append(
                ScoredSkill(
                    skill_id=gap.skill_id,
                    label=gap.label,
                    priority=priority,
                    mastery=gap.mastery,
                    gap=gap.gap,
                    difficulty=gap.difficulty,
                    blocked=gap.blocked,
                    blocked_by=gap.blocked_by,
                    reason=self._build_reason(gap),
                )
            )

        scored.sort(
            key=lambda item: item.priority,
            reverse=True,
        )

        return scored

    def _calculate_priority(
        self,
        gap: SkillGap,
    ) -> float:

        gap_score = gap.gap

        difficulty_score = (
            1.0 / (1.0 + gap.difficulty)
        )

        return (
            gap_score * 0.7
            + difficulty_score * 0.3
        )

    def _build_reason(
        self,
        gap: SkillGap,
    ) -> str:

        return (
            f"{gap.label} is actionable because "
            f"its prerequisites are currently satisfied "
            f"and its mastery is {gap.mastery:.0%}."
        )