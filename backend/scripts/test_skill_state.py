from app.db.database import SessionLocal
from app.services.learner.skill_state import LearnerSkillStateService


def main() -> None:
    with SessionLocal() as db:
        service = LearnerSkillStateService(db)

        state = service.create(
            learner_id="demo-user",
            skill_id="rest",
        )

        print("Skill state created:")
        print(f"Learner: {state.learner_id}")
        print(f"Skill: {state.skill_id}")
        print(f"Theta: {state.theta}")
        print(f"Confidence: {state.confidence}")
        print(f"Mastery: {state.mastery}")
        print(f"Status: {state.status}")

        updated = service.update(
            learner_id="demo-user",
            skill_id="rest",
            theta=-0.7,
            confidence=0.65,
            mastery=0.42,
            status="learning",
        )

        print("\nUpdated skill state:")
        print(f"Theta: {updated.theta}")
        print(f"Confidence: {updated.confidence}")
        print(f"Mastery: {updated.mastery}")
        print(f"Status: {updated.status}")


if __name__ == "__main__":
    main()