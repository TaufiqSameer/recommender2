from app.db.database import SessionLocal

from app.services.knowledge.repository import (
    KnowledgeRepository,
)

from app.services.skill_graph.integrator import (
    KnowledgeGraphIntegrator,
)


def main():

    with SessionLocal() as db:

        repository = KnowledgeRepository(db)

        integrator = KnowledgeGraphIntegrator(db)

        # -----------------------------------------
        # Find our existing Actix Web candidate
        # -----------------------------------------

        candidates = (
            repository.get_candidates_by_concept(
                "Actix Web"
            )
        )

        if not candidates:
            print(
                "Actix Web candidate not found."
            )
            return

        candidate = candidates[-1]

        print("=== CANDIDATE ===")

        print(
            f"ID: {candidate.id}"
        )

        print(
            f"Concept: {candidate.concept}"
        )

        print(
            f"Status: "
            f"{candidate.verification_status}"
        )

        print(
            f"Confidence: "
            f"{candidate.confidence}"
        )

        # -----------------------------------------
        # Integrate into skill graph
        # -----------------------------------------

        print("\n=== INTEGRATING ===")

        try:

            skill = integrator.integrate(
                candidate.id
            )

            print(
                f"Skill created: "
                f"{skill.label}"
            )

            print(
                f"Skill ID: "
                f"{skill.id}"
            )

        except Exception as error:

            print(
                f"Integration rejected:"
            )

            print(error)


if __name__ == "__main__":
    main()