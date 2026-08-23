from app.db.database import SessionLocal

from app.services.skill_graph.acquisition import (
    KnowledgeGraphAcquisitionService,
)


def main():

    with SessionLocal() as db:

        service = (
            KnowledgeGraphAcquisitionService(
                db
            )
        )

        print(
            "=== RECURSIVE GRAPH ACQUISITION ==="
        )

        try:

            skill = service.acquire_skill(
                concept="Axum",
                domain="backend",
            )

            print(
                "\nSUCCESS"
            )

            print(
                f"Skill: {skill.label}"
            )

            print(
                f"ID: {skill.id}"
            )

        except Exception as error:

            print(
                "\nACQUISITION FAILED"
            )

            print(error)


if __name__ == "__main__":
    main()