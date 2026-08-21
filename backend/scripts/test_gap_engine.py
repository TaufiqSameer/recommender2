from app.db.database import SessionLocal
from app.services.learner.skill_state import (
    LearnerSkillStateService,
)
from app.services.recommendation.gap_engine import (
    SkillGapEngine,
)


def main() -> None:

    learner_id = "gap-demo"

    with SessionLocal() as db:

        skill_service = LearnerSkillStateService(db)

        # Existing knowledge.
        mastered = [
            "programming-fundamentals",
            "git",
            "linux",
            "networking",
        ]

        for skill_id in mastered:

            state = skill_service.get(
                learner_id,
                skill_id,
            )

            if state is None:
                state = skill_service.create(
                    learner_id,
                    skill_id,
                )

            skill_service.update(
                learner_id,
                skill_id,
                mastery=0.95,
                confidence=0.9,
                theta=1.5,
                status="mastered",
            )

        # HTTP is partially known.
        state = skill_service.get(
            learner_id,
            "http",
        )

        if state is None:
            state = skill_service.create(
                learner_id,
                "http",
            )

        skill_service.update(
            learner_id,
            "http",
            mastery=0.4,
            confidence=0.7,
            theta=-0.2,
            status="learning",
        )

        # REST is weak.
        state = skill_service.get(
            learner_id,
            "rest",
        )

        if state is None:
            state = skill_service.create(
                learner_id,
                "rest",
            )

        skill_service.update(
            learner_id,
            "rest",
            mastery=0.2,
            confidence=0.8,
            theta=-1.0,
            status="learning",
        )

        engine = SkillGapEngine(db)

        gaps = engine.analyze(
            learner_id=learner_id,
            target_skill_ids={"fastapi"},
        )

        print("\nSkill gaps:\n")

        for gap in gaps:

            print(
                f"{gap.label}"
            )

            print(
                f"  mastery: {gap.mastery:.0%}"
            )

            print(
                f"  gap: {gap.gap:.0%}"
            )

            print(
                f"  blocked: {gap.blocked}"
            )

            print(
                f"  blocked_by: {gap.blocked_by}"
            )

            print()


if __name__ == "__main__":
    main()