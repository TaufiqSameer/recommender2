from app.db.database import SessionLocal

from app.db.models.assessment import AssessmentAttempt
from app.db.models import LearnerEvidence

from app.services.assessment.evidence import (
    AssessmentEvidenceService,
)


def main():

    db = SessionLocal()

    try:

        attempt_id = "http-attempt-001"

        # -----------------------------------------
        # Get completed assessment attempt
        # -----------------------------------------

        attempt = (
            db.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.id == attempt_id
            )
            .first()
        )

        if attempt is None:
            raise RuntimeError(
                "Assessment attempt not found. "
                "Run test_assessment_evaluator first."
            )

        print("=== ASSESSMENT ATTEMPT ===")

        print(
            f"Learner: {attempt.learner_id}"
        )

        print(
            f"Assessment: {attempt.assessment_id}"
        )

        print(
            f"Score: {attempt.score:.2f}"
        )

        # -----------------------------------------
        # Create learner evidence
        # -----------------------------------------

        service = AssessmentEvidenceService(db)

        evidence = service.record_attempt(
            attempt=attempt,
            skill_id="http",
        )

        print("\n=== EVIDENCE CREATED ===")

        print(
            f"ID: {evidence.id}"
        )

        print(
            f"Learner: {evidence.learner_id}"
        )

        print(
            f"Skill: {evidence.skill_id}"
        )

        print(
            f"Type: {evidence.evidence_type}"
        )

        print(
            f"Source: {evidence.source_id}"
        )

        print(
            f"Score: {evidence.score:.2f}"
        )

        # -----------------------------------------
        # Verify database
        # -----------------------------------------

        stored = (
            db.query(LearnerEvidence)
            .filter(
                LearnerEvidence.id
                == evidence.id
            )
            .first()
        )

        print("\n=== DATABASE VERIFICATION ===")

        print(
            f"Evidence found: "
            f"{stored is not None}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()