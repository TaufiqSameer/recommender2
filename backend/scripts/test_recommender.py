from app.db.database import SessionLocal

from app.services.learning.recommender import (
    LearningRecommender,
)


def main():

    db = SessionLocal()

    try:

        learner_id = "learner-001"

        recommender = LearningRecommender(
            db
        )

        recommendations = recommender.recommend(
            learner_id=learner_id,
            limit=5,
        )

        print(
            "=== LEARNING RECOMMENDATIONS ==="
        )

        if not recommendations:

            print(
                "No learning recommendations available."
            )

            return

        for index, recommendation in enumerate(
            recommendations,
            start=1,
        ):

            skill = recommendation.skill
            breakdown = recommendation.breakdown

            print(
                f"\n{index}. {skill.label}"
            )

            print(
                f"   ID: {skill.id}"
            )

            print(
                f"   Score: "
                f"{recommendation.score:.3f}"
            )

            print(
                "   Breakdown:"
            )

            print(
                f"      Level fit: "
                f"{breakdown.level_fit:.3f}"
            )

            print(
                f"      Mastery gap: "
                f"{breakdown.mastery_gap:.3f}"
            )

            print(
                f"      Prerequisite readiness: "
                f"{breakdown.prerequisite_readiness:.3f}"
            )

            print(
                f"      Unlock value: "
                f"{breakdown.unlock_value:.3f}"
            )

            print(
                f"      Exploration: "
                f"{breakdown.exploration:.3f}"
            )

            print(
                f"   Reason: "
                f"{recommendation.reason}"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()