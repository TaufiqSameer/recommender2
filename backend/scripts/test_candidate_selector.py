from app.db.database import SessionLocal

from app.db.models import LearnerSkillState

from app.services.learning.candidate_selector import (
    CandidateSelector,
)


def main():

    db = SessionLocal()

    try:

        learner_id = "learner-001"

        selector = CandidateSelector(db)

        # =====================================================
        # 1. ELIGIBLE CANDIDATES
        # =====================================================

        candidates = selector.get_candidates(
            learner_id
        )

        print(
            "=== LEARNING CANDIDATES ==="
        )

        if not candidates:

            print(
                "No eligible skills found."
            )

        else:

            for candidate in candidates:

                skill = candidate.skill

                print(
                    f"\nSkill: {skill.label}"
                )

                print(
                    f"ID: {skill.id}"
                )

                if candidate.mastery is None:

                    print(
                        "Mastery: no evidence"
                    )

                else:

                    print(
                        f"Mastery: "
                        f"{candidate.mastery:.3f}"
                    )

                print(
                    f"Prerequisites: "
                    f"{candidate.prerequisite_count}"
                )

                print(
                    f"Potential unlocks: "
                    f"{candidate.unlocked_skill_count}"
                )

        # =====================================================
        # 2. COMPLETE GRAPH STATUS
        # =====================================================

        statuses = selector.get_skill_status(
            learner_id
        )

        print(
            "\n\n=== SKILL GRAPH STATUS ==="
        )

        for status in statuses:

            print(
                f"\nSkill: "
                f"{status.skill.label}"
            )

            print(
                f"ID: "
                f"{status.skill.id}"
            )

            # -------------------------------------------------
            # Mastery
            # -------------------------------------------------

            if status.mastery is None:

                print(
                    "Mastery: no evidence"
                )

            else:

                print(
                    f"Mastery: "
                    f"{status.mastery:.3f}"
                )

            # -------------------------------------------------
            # Eligibility
            # -------------------------------------------------

            if status.eligible:

                print(
                    "Eligible: YES"
                )

            else:

                print(
                    "Eligible: NO"
                )

            # -------------------------------------------------
            # Prerequisites
            # -------------------------------------------------

            if not status.prerequisites:

                print(
                    "Prerequisites: none"
                )

                continue

            print(
                "Prerequisites:"
            )

            for prerequisite_id in (
                status.prerequisites
            ):

                if (
                    prerequisite_id
                    in status.satisfied_prerequisites
                ):

                    print(
                        f"  ✓ {prerequisite_id}"
                    )

                else:

                    print(
                        f"  ✗ {prerequisite_id}"
                    )

            # -------------------------------------------------
            # Missing prerequisites
            # -------------------------------------------------

            if status.unsatisfied_prerequisites:

                print(
                    "Blocked by:"
                )

                for prerequisite_id in (
                    status.unsatisfied_prerequisites
                ):

                    print(
                        f"  → {prerequisite_id}"
                    )

    finally:

        db.close()


if __name__ == "__main__":
    main()