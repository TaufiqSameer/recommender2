from app.db.database import SessionLocal

from app.services.learning.feedback import (
    LearningFeedbackService,
)

from app.services.learning.candidate_selector import (
    CandidateSelector,
)


LEARNER_ID = "progression-test-001"

MASTERY_THRESHOLD = 0.70


def print_candidates(
    selector: CandidateSelector,
    learner_id: str,
    title: str,
):
    candidates = selector.get_candidates(
        learner_id
    )

    print(
        f"\n=== {title} ==="
    )

    if not candidates:

        print(
            "No eligible skills."
        )

        return

    for candidate in candidates:

        print(
            f"\n{candidate.skill.label}"
        )

        print(
            f"  ID: "
            f"{candidate.skill.id}"
        )

        if candidate.mastery is None:

            print(
                "  Mastery: no evidence"
            )

        else:

            print(
                f"  Mastery: "
                f"{candidate.mastery:.3f}"
            )

        print(
            f"  Prerequisites: "
            f"{candidate.prerequisite_count}"
        )

        print(
            f"  Potential unlocks: "
            f"{candidate.unlocked_skill_count}"
        )


def submit_evidence(
    feedback: LearningFeedbackService,
    learner_id: str,
    skill_id: str,
    score: float,
    attempt: int,
):
    print(
        "\n----------------------------------------"
    )

    print(
        "Submitting evidence:"
    )

    print(
        f"  Skill: {skill_id}"
    )

    print(
        f"  Score: {score:.3f}"
    )

    print(
        f"  Attempt: {attempt}"
    )

    result = feedback.process(
        learner_id=learner_id,
        skill_id=skill_id,
        score=score,
        evidence_type="assessment",
        source_id=(
            f"progression-{skill_id}-{attempt}"
        ),
        metadata={
            "test": "progression",
            "attempt": attempt,
        },
    )

    state = result.state

    print(
        "\nUpdated state:"
    )

    print(
        f"  Mastery: "
        f"{state.mastery:.3f}"
    )

    print(
        f"  Theta: "
        f"{state.theta:.3f}"
    )

    print(
        f"  Confidence: "
        f"{state.confidence:.3f}"
    )

    print(
        f"  Attempts: "
        f"{state.attempts}"
    )

    print(
        f"  Status: "
        f"{state.status}"
    )

    return state


def build_mastery(
    feedback: LearningFeedbackService,
    learner_id: str,
    skill_id: str,
    target: float = MASTERY_THRESHOLD,
):
    """
    Keep submitting strong evidence until the learner
    crosses the prerequisite mastery threshold.

    With the current learning rate of 0.30, one 0.95
    assessment is not enough.

    This function therefore does NOT assume that:

        score == mastery

    Instead, it keeps feeding evidence until:

        mastery >= target
    """

    attempt = 1

    while True:

        state = submit_evidence(
            feedback=feedback,
            learner_id=learner_id,
            skill_id=skill_id,
            score=0.95,
            attempt=attempt,
        )

        if state.mastery >= target:

            print(
                f"\n✓ {skill_id} reached "
                f"{state.mastery:.3f} mastery."
            )

            return state

        print(
            f"\n{skill_id} has not reached "
            f"{target:.2f} mastery yet."
        )

        attempt += 1


def main():

    db = SessionLocal()

    try:

        feedback = LearningFeedbackService(
            db
        )

        selector = CandidateSelector(
            db
        )

        # =================================================
        # STEP 1
        # Initial graph state
        # =================================================

        print_candidates(
            selector,
            LEARNER_ID,
            "INITIAL CANDIDATES",
        )

        # =================================================
        # STEP 2
        # Master Programming Fundamentals
        # =================================================

        build_mastery(
            feedback,
            LEARNER_ID,
            "programming-fundamentals",
        )

        print_candidates(
            selector,
            LEARNER_ID,
            "AFTER PROGRAMMING FUNDAMENTALS",
        )

        # =================================================
        # STEP 3
        # Master Linux
        # =================================================

        build_mastery(
            feedback,
            LEARNER_ID,
            "linux",
        )

        print_candidates(
            selector,
            LEARNER_ID,
            "AFTER LINUX",
        )

        # =================================================
        # STEP 4
        # Master Networking
        # =================================================

        build_mastery(
            feedback,
            LEARNER_ID,
            "networking",
        )

        print_candidates(
            selector,
            LEARNER_ID,
            "AFTER NETWORKING",
        )

        # =================================================
        # STEP 5
        # Master HTTP
        # =================================================

        build_mastery(
            feedback,
            LEARNER_ID,
            "http",
        )

        print_candidates(
            selector,
            LEARNER_ID,
            "AFTER HTTP",
        )

        # =================================================
        # STEP 6
        # Master REST
        # =================================================

        build_mastery(
            feedback,
            LEARNER_ID,
            "rest",
        )

        print_candidates(
            selector,
            LEARNER_ID,
            "AFTER REST",
        )

        # =================================================
        # STEP 7
        # Master API Design
        # =================================================

        build_mastery(
            feedback,
            LEARNER_ID,
            "api-design",
        )

        print_candidates(
            selector,
            LEARNER_ID,
            "AFTER API DESIGN",
        )

        # =================================================
        # STEP 8
        # Build PostgreSQL dependency chain
        #
        # SQL
        #   ↓
        # Data Modeling
        #   ↓
        # PostgreSQL
        # =================================================

        build_mastery(
            feedback,
            LEARNER_ID,
            "sql",
        )

        build_mastery(
            feedback,
            LEARNER_ID,
            "data-modeling",
        )

        build_mastery(
            feedback,
            LEARNER_ID,
            "postgresql",
        )

        print_candidates(
            selector,
            LEARNER_ID,
            "AFTER POSTGRESQL",
        )

        # =================================================
        # STEP 9
        # FastAPI should now be eligible because:
        #
        # API Design >= 0.70
        # AND
        # PostgreSQL >= 0.70
        # =================================================

        print(
            "\n========================================"
        )

        print(
            "CHECKING FASTAPI ELIGIBILITY"
        )

        print(
            "========================================"
        )

        statuses = selector.get_skill_status(
            LEARNER_ID
        )

        fastapi_status = next(
            status
            for status in statuses
            if status.skill.id == "fastapi"
        )

        print(
            f"\nFastAPI eligible: "
            f"{fastapi_status.eligible}"
        )

        print(
            "Satisfied prerequisites:"
        )

        for prerequisite in (
            fastapi_status.satisfied_prerequisites
        ):

            print(
                f"  ✓ {prerequisite}"
            )

        print(
            "Unsatisfied prerequisites:"
        )

        if not fastapi_status.unsatisfied_prerequisites:

            print(
                "  None"
            )

        else:

            for prerequisite in (
                fastapi_status.unsatisfied_prerequisites
            ):

                print(
                    f"  ✗ {prerequisite}"
                )

        # =================================================
        # STEP 10
        # FastAPI should be eligible.
        #
        # We now give the learner evidence for it.
        # =================================================

        if fastapi_status.eligible:

            build_mastery(
                feedback,
                LEARNER_ID,
                "fastapi",
            )

        else:

            print(
                "\nFastAPI is still blocked."
            )

            print(
                "The prerequisite graph is preventing "
                "the learner from progressing."
            )

        # =================================================
        # FINAL GRAPH
        # =================================================

        print_candidates(
            selector,
            LEARNER_ID,
            "FINAL CANDIDATES",
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()