from app.db.database import SessionLocal

from app.db.models.learner import (
    LearnerEvidence,
    LearnerSkillState,
)

from app.services.learner.model import (
    LearnerModelService,
)


def main():

    db = SessionLocal()

    try:

        # -----------------------------------------
        # Find the assessment evidence we created
        # earlier.
        # -----------------------------------------

        evidence = (
            db.query(LearnerEvidence)
            .filter(
                LearnerEvidence.learner_id
                == "learner-001",
                LearnerEvidence.skill_id
                == "http",
                LearnerEvidence.evidence_type
                == "assessment",
            )
            .order_by(
                LearnerEvidence.created_at.desc()
            )
            .first()
        )

        if evidence is None:
            raise RuntimeError(
                "No HTTP assessment evidence found."
            )

        print("=== EVIDENCE ===")

        print(
            f"Learner: "
            f"{evidence.learner_id}"
        )

        print(
            f"Skill: "
            f"{evidence.skill_id}"
        )

        print(
            f"Score: "
            f"{evidence.score:.2f}"
        )

        # -----------------------------------------
        # Update learner model
        # -----------------------------------------

        service = LearnerModelService(db)

        state = (
            service.update_from_evidence(
                evidence=evidence
            )
        )

        # -----------------------------------------
        # Display learner state
        # -----------------------------------------

        print(
            "\n=== LEARNER SKILL STATE ==="
        )

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

        # -----------------------------------------
        # Verify database
        # -----------------------------------------

        stored = (
            db.query(LearnerSkillState)
            .filter(
                LearnerSkillState.learner_id
                == "learner-001",
                LearnerSkillState.skill_id
                == "http",
            )
            .first()
        )

        print(
            "\n=== DATABASE VERIFICATION ==="
        )

        print(
            f"State found: "
            f"{stored is not None}"
        )

        if stored:

            print(
                f"Stored mastery: "
                f"{stored.mastery:.3f}"
            )

            print(
                f"Stored theta: "
                f"{stored.theta:.3f}"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()