from app.db.database import SessionLocal

from app.services.learning.feedback import (
    LearningFeedbackService,
)


def main():

    db = SessionLocal()

    try:

        learner_id = "learner-001"
        skill_id = "http"

        feedback = LearningFeedbackService(
            db
        )

        # -----------------------------------------
        # Simulate new learning evidence
        # -----------------------------------------

        result = feedback.process(
            learner_id=learner_id,
            skill_id=skill_id,
            score=0.90,
            evidence_type="assessment",
            source_id="http-attempt-002",
            metadata={
                "assessment_id": "http-baseline-002",
            },
        )

        # -----------------------------------------
        # Display evidence
        # -----------------------------------------

        print(
            "=== FEEDBACK ==="
        )

        print(
            f"Learner: "
            f"{result.evidence.learner_id}"
        )

        print(
            f"Skill: "
            f"{result.evidence.skill_id}"
        )

        print(
            f"Evidence score: "
            f"{result.evidence.score:.3f}"
        )

        # -----------------------------------------
        # Display updated learner model
        # -----------------------------------------

        print(
            "\n=== UPDATED LEARNER MODEL ==="
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

    finally:

        db.close()


if __name__ == "__main__":
    main()