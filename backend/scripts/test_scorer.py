from app.db.database import SessionLocal
from app.services.recommendation.gap_engine import (
    SkillGapEngine,
)
from app.services.recommendation.scorer import (
    SkillScorer,
)


def main() -> None:

    learner_id = "gap-demo"

    with SessionLocal() as db:

        gap_engine = SkillGapEngine(db)

        gaps = gap_engine.analyze(
            learner_id=learner_id,
            target_skill_ids={"fastapi"},
        )

        scorer = SkillScorer()

        recommendations = scorer.score(
            gaps
        )

        print("\nActionable recommendations:\n")

        for index, recommendation in enumerate(
            recommendations,
            start=1,
        ):

            print(
                f"{index}. "
                f"{recommendation.label}"
            )

            print(
                f"   priority: "
                f"{recommendation.priority:.3f}"
            )

            print(
                f"   mastery: "
                f"{recommendation.mastery:.0%}"
            )

            print(
                f"   gap: "
                f"{recommendation.gap:.0%}"
            )

            print(
                f"   reason: "
                f"{recommendation.reason}"
            )

            print()


if __name__ == "__main__":
    main()