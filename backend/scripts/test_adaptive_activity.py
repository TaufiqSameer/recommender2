from app.db.database import SessionLocal

from app.services.learning.activity import (
    LearningActivityService,
)


LEARNER_ID = "ranking-test-002"


def main():

    db = SessionLocal()

    try:

        service = (
            LearningActivityService(db)
        )

        result = (
            service.generate_next_activity(
                LEARNER_ID
            )
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "ADAPTIVE LEARNING ACTIVITY"
        )

        print(
            "=" * 70
        )

        if result is None:

            print(
                "\nNo learning activity available."
            )

            return

        recommendation = (
            result["recommendation"]
        )

        activity = (
            result["activity"]
        )

        # =================================================
        # ADAPTIVE ENGINE DECISION
        # =================================================

        print(
            "\nRECOMMENDER DECISION"
        )

        print(
            f"  Skill: "
            f"{recommendation.skill.label}"
        )

        print(
            f"  ID: "
            f"{recommendation.skill.id}"
        )

        print(
            f"  Score: "
            f"{recommendation.score:.3f}"
        )

        print(
            f"  Reason: "
            f"{recommendation.reason}"
        )

        # =================================================
        # GEMINI DECISION
        # =================================================

        print(
            "\nGEMINI LEARNING ACTIVITY"
        )

        print(
            f"\n  Title:"
            f"\n    {activity.title}"
        )

        print(
            f"\n  Type:"
            f"\n    {activity.activity_type}"
        )

        print(
            f"\n  Objective:"
            f"\n    {activity.objective}"
        )

        print(
            f"\n  Difficulty:"
            f"\n    {activity.difficulty}"
        )

        print(
            f"\n  Instructions:"
            f"\n    {activity.instructions}"
        )

        print(
            "\n  Hints:"
        )

        if not activity.hints:

            print(
                "    No hints provided."
            )

        else:

            for index, hint in enumerate(
                activity.hints,
                start=1,
            ):

                print(
                    f"    {index}. {hint}"
                )

        print(
            "\n"
            + "=" * 70
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()