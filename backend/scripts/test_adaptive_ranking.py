from app.db.database import SessionLocal

from app.services.learning.feedback import (
    LearningFeedbackService,
)

from app.services.learning.recommender import (
    LearningRecommender,
)


LEARNER_ID = "ranking-test-002"


def print_recommendations(
    recommender,
    title,
):
    recommendations = recommender.recommend(
        learner_id=LEARNER_ID,
        limit=5,
    )

    print(
        f"\n{'=' * 60}"
    )

    print(title)

    print(
        f"{'=' * 60}"
    )

    if not recommendations:

        print(
            "No recommendations."
        )

        return

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):

        breakdown = recommendation.breakdown

        print(
            f"\n{index}. "
            f"{recommendation.skill.label}"
        )

        print(
            f"   ID: "
            f"{recommendation.skill.id}"
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


def master_skill(
    feedback,
    skill_id,
    score=0.95,
    max_attempts=10,
):
    print(
        "\n"
        + "=" * 60
    )

    print(
        f"MASTERING SKILL: {skill_id}"
    )

    print(
        "=" * 60
    )

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        result = feedback.process(
            learner_id=LEARNER_ID,
            skill_id=skill_id,
            score=score,
            evidence_type="assessment",
            source_id=(
                f"ranking-test-"
                f"{skill_id}-"
                f"mastery-{attempt}"
            ),
            metadata={
                "test": "adaptive-ranking",
                "purpose": "mastery",
                "attempt": attempt,
            },
        )

        state = result.state

        print(
            f"Attempt {attempt}: "
            f"mastery={state.mastery:.3f}, "
            f"confidence={state.confidence:.3f}, "
            f"status={state.status}"
        )

        if state.status == "mastered":

            print(
                f"\n✓ {skill_id} mastered "
                f"after {attempt} attempts."
            )

            return state

    raise RuntimeError(
        f"{skill_id} did not reach mastery "
        f"within {max_attempts} attempts."
    )


def main():

    db = SessionLocal()

    try:

        feedback = LearningFeedbackService(
            db
        )

        recommender = LearningRecommender(
            db
        )

        # =================================================
        # STAGE 1
        #
        # Completely new learner.
        # =================================================

        print_recommendations(
            recommender,
            "STAGE 1 — NEW LEARNER",
        )

        # =================================================
        # STAGE 2
        #
        # Master Programming Fundamentals.
        #
        # Expected:
        #
        # Programming Fundamentals should disappear
        # from recommendations once mastered.
        #
        # Skills depending on it should become eligible.
        # =================================================

        master_skill(
            feedback,
            "programming-fundamentals",
        )

        print_recommendations(
            recommender,
            "STAGE 2 — AFTER PROGRAMMING FUNDAMENTALS",
        )

        # =================================================
        # STAGE 3
        #
        # Master Linux.
        #
        # Expected:
        #
        # Networking should now become eligible.
        # =================================================

        master_skill(
            feedback,
            "linux",
        )

        print_recommendations(
            recommender,
            "STAGE 3 — AFTER LINUX",
        )

        # =================================================
        # STAGE 4
        #
        # Master Networking.
        #
        # Expected:
        #
        # HTTP should now become eligible.
        # =================================================

        master_skill(
            feedback,
            "networking",
        )

        print_recommendations(
            recommender,
            "STAGE 4 — AFTER NETWORKING",
        )

        # =================================================
        # STAGE 5
        #
        # Master HTTP.
        #
        # Expected:
        #
        # REST should now become eligible.
        #
        # Authentication may also become eligible depending
        # on its other prerequisites.
        # =================================================

        master_skill(
            feedback,
            "http",
        )

        print_recommendations(
            recommender,
            "STAGE 5 — AFTER HTTP",
        )

        # =================================================
        # STAGE 6
        #
        # Master REST.
        #
        # Expected:
        #
        # API Design should now become eligible.
        # =================================================

        master_skill(
            feedback,
            "rest",
        )

        print_recommendations(
            recommender,
            "STAGE 6 — AFTER REST",
        )

        # =================================================
        # STAGE 7
        #
        # Master API Design.
        #
        # PostgreSQL is still not mastered, so FastAPI
        # should remain blocked.
        # =================================================

        master_skill(
            feedback,
            "api-design",
        )

        print_recommendations(
            recommender,
            "STAGE 7 — AFTER API DESIGN",
        )

        # =================================================
        # STAGE 8
        #
        # Build the PostgreSQL branch.
        #
        # SQL
        #   ↓
        # Data Modeling
        #   ↓
        # PostgreSQL
        # =================================================

        master_skill(
            feedback,
            "sql",
        )

        master_skill(
            feedback,
            "data-modeling",
        )

        master_skill(
            feedback,
            "postgresql",
        )

        print_recommendations(
            recommender,
            "STAGE 8 — AFTER POSTGRESQL",
        )

        # =================================================
        # STAGE 9
        #
        # Both FastAPI prerequisites should now be mastered:
        #
        # API Design
        # PostgreSQL
        #
        # Therefore FastAPI should become eligible.
        # =================================================

        print(
            "\n"
            + "=" * 60
        )

        print(
            "FINAL EXPECTATION"
        )

        print(
            "=" * 60
        )

        print(
            "FastAPI should now be eligible because:"
        )

        print(
            "  ✓ API Design is mastered"
        )

        print(
            "  ✓ PostgreSQL is mastered"
        )

        print(
            "  ✓ FastAPI itself has not been mastered"
        )

        print_recommendations(
            recommender,
            "STAGE 9 — FINAL GRAPH STATE",
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()