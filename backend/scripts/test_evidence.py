from app.db.database import SessionLocal
from app.services.learner.evidence import LearnerEvidenceService


def main() -> None:
    with SessionLocal() as db:
        service = LearnerEvidenceService(db)

        evidence = service.record(
            learner_id="demo-user",
            skill_id="rest",
            evidence_type="assessment",
            source_id="assessment-001",
            score=0.6,
            metadata={
                "question_count": 5,
                "correct": 3,
            },
        )

        print("Evidence created:")
        print(f"ID: {evidence.id}")
        print(f"Learner: {evidence.learner_id}")
        print(f"Skill: {evidence.skill_id}")
        print(f"Type: {evidence.evidence_type}")
        print(f"Score: {evidence.score}")

        evidence_list = service.get_for_skill(
            learner_id="demo-user",
            skill_id="rest",
        )

        print("\nEvidence for REST:")

        for item in evidence_list:
            print(
                f"- {item.evidence_type}: "
                f"{item.score}"
            )


if __name__ == "__main__":
    main()