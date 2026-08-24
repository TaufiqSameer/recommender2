from app.db.database import SessionLocal

from app.services.learning.feedback import (
    LearningFeedbackService,
)

from app.services.learning.recommender import (
    LearningRecommender,
)

from app.services.learning.candidate_selector import (
    CandidateSelector,
)


def print_recommendations(
    title,
    recommendations,
):
    print(f"\n=== {title} ===")

    if not recommendations:
        print("No recommendations.")
        return

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):

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
            f"   Reason: "
            f"{recommendation.reason}"
        )


def get_candidate_ids(candidates):
    """
    Convert LearningCandidate objects into
    a set of skill IDs.

    Example:

        [
            LearningCandidate(skill=HTTP),
            LearningCandidate(skill=REST)
        ]

    becomes:

        {
            "http",
            "rest"
        }
    """

    return {
        candidate.skill.id
        for candidate in candidates
    }


def print_graph_state_before(candidates):
    """
    Show whether HTTP's dependent skills are
    currently eligible.
    """

    candidate_ids = get_candidate_ids(
        candidates
    )

    print(
        "\n=== GRAPH STATE BEFORE FEEDBACK ==="
    )

    print(
        "REST:",
        "ELIGIBLE"
        if "rest" in candidate_ids
        else "BLOCKED",
    )

    print(
        "Authentication:",
        "ELIGIBLE"
        if "authentication" in candidate_ids
        else "BLOCKED",
    )


def print_graph_transition(
    before_candidates,
    after_candidates,
):
    """
    Compare graph eligibility before and
    after learner feedback.
    """

    before_ids = get_candidate_ids(
        before_candidates
    )

    after_ids = get_candidate_ids(
        after_candidates
    )

    print(
        "\n=== GRAPH TRANSITION ==="
    )

    # -----------------------------------------
    # REST
    # -----------------------------------------

    print(
        "REST before:",
        "YES"
        if "rest" in before_ids
        else "NO",
    )

    print(
        "REST after:",
        "YES"
        if "rest" in after_ids
        else "NO",
    )

    # -----------------------------------------
    # Authentication
    # -----------------------------------------

    print(
        "Authentication before:",
        "YES"
        if "authentication" in before_ids
        else "NO",
    )

    print(
        "Authentication after:",
        "YES"
        if "authentication" in after_ids
        else "NO",
    )


def main():

    db = SessionLocal()

    try:

        learner_id = "learner-001"

        # -----------------------------------------
        # Services
        # -----------------------------------------

        recommender = LearningRecommender(
            db
        )

        feedback = LearningFeedbackService(
            db
        )

        selector = CandidateSelector(
            db
        )

        # =====================================================
        # STEP 1
        # Recommendations BEFORE feedback
        # =====================================================

        before = recommender.recommend(
            learner_id=learner_id,
            limit=5,
        )

        print_recommendations(
            "RECOMMENDATIONS BEFORE FEEDBACK",
            before,
        )

        # =====================================================
        # STEP 2
        # Candidate graph BEFORE feedback
        # =====================================================

        candidates_before = (
            selector.get_candidates(
                learner_id
            )
        )

        print_graph_state_before(
            candidates_before
        )

        # =====================================================
        # STEP 3
        # Simulate learner completing an
        # HTTP assessment.
        #
        # A high score should increase HTTP
        # mastery.
        # =====================================================

        result = feedback.process(
            learner_id=learner_id,
            skill_id="http",
            score=0.95,
            evidence_type="assessment",
            source_id="http-adaptive-test-001",
            metadata={
                "assessment_id":
                    "http-adaptive-test-001",
            },
        )

        # =====================================================
        # STEP 4
        # Show updated learner state
        # =====================================================

        print(
            "\n=== UPDATED LEARNER STATE ==="
        )

        state = result.state

        print(
            f"Learner: "
            f"{state.learner_id}"
        )

        print(
            f"Skill: "
            f"{state.skill_id}"
        )

        print(
            f"Mastery: "
            f"{state.mastery:.3f}"
        )

        print(
            f"Theta: "
            f"{state.theta:.3f}"
        )

        print(
            f"Confidence: "
            f"{state.confidence:.3f}"
        )

        print(
            f"Attempts: "
            f"{state.attempts}"
        )

        print(
            f"Status: "
            f"{state.status}"
        )

        # =====================================================
        # STEP 5
        # Recalculate candidates AFTER feedback
        #
        # IMPORTANT:
        #
        # CandidateSelector queries the database again,
        # so it sees the UPDATED learner state.
        # =====================================================

        candidates_after = (
            selector.get_candidates(
                learner_id
            )
        )

        print_graph_transition(
            candidates_before,
            candidates_after,
        )

        # =====================================================
        # STEP 6
        # Generate recommendations AFTER feedback
        # =====================================================

        after = recommender.recommend(
            learner_id=learner_id,
            limit=5,
        )

        print_recommendations(
            "RECOMMENDATIONS AFTER FEEDBACK",
            after,
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()