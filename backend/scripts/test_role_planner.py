from app.db.database import SessionLocal
from app.services.learner.skill_state import (
    LearnerSkillStateService,
)
from app.services.planner.path_planner import (
    LearningPathPlanner,
)


def main() -> None:
    learner_id = "role-demo"

    with SessionLocal() as db:
        skill_service = LearnerSkillStateService(db)

        # Skills this learner already knows.
        mastered_skills = [
            "programming-fundamentals",
            "git",
            "linux",
            "networking",
        ]

        for skill_id in mastered_skills:
            state = skill_service.get(
                learner_id,
                skill_id,
            )

            if state is None:
                skill_service.create(
                    learner_id,
                    skill_id,
                )

            skill_service.update(
                learner_id,
                skill_id,
                theta=1.5,
                confidence=0.9,
                mastery=0.95,
                status="mastered",
            )

        # HTTP is partially understood.
        state = skill_service.get(
            learner_id,
            "http",
        )

        if state is None:
            skill_service.create(
                learner_id,
                "http",
            )

        skill_service.update(
            learner_id,
            "http",
            theta=-0.2,
            confidence=0.7,
            mastery=0.4,
            status="learning",
        )

        # REST is weak.
        state = skill_service.get(
            learner_id,
            "rest",
        )

        if state is None:
            skill_service.create(
                learner_id,
                "rest",
            )

        skill_service.update(
            learner_id,
            "rest",
            theta=-1.0,
            confidence=0.8,
            mastery=0.2,
            status="learning",
        )

        planner = LearningPathPlanner(db)

        path = planner.build_path_for_role(
            learner_id=learner_id,
            role_id="backend-engineer",
            max_steps=10,
        )

        print(
            "\nRecommended path for "
            "Backend Engineer:\n"
        )

        for index, recommendation in enumerate(
            path,
            start=1,
        ):
            print(
                f"{index}. "
                f"{recommendation.label}"
            )

            print(
                f"   mastery: "
                f"{recommendation.mastery:.0%}"
            )

            print(
                f"   difficulty: "
                f"{recommendation.difficulty}"
            )

            print(
                f"   reason: "
                f"{recommendation.reason}"
            )


if __name__ == "__main__":
    main()