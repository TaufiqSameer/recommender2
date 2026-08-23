from app.db.database import SessionLocal

from app.services.knowledge.retriever import (
    KnowledgeRetriever,
)


def main():

    with SessionLocal() as db:

        retriever = KnowledgeRetriever(db)

        # -----------------------------
        # Test 1: Existing skill
        # -----------------------------

        print("=== EXISTING SKILL ===")

        result = retriever.retrieve(
            "FastAPI"
        )

        print(f"Found: {result.found}")
        print(f"Source: {result.source}")

        if result.skill:
            print(
                f"Skill: {result.skill.label}"
            )

        # -----------------------------
        # Test 2: Verified candidate
        # -----------------------------

        print("\n=== VERIFIED CANDIDATE ===")

        result = retriever.retrieve(
            "GraphQL"
        )

        print(f"Found: {result.found}")
        print(f"Source: {result.source}")

        if result.candidate:
            print(
                f"Concept: "
                f"{result.candidate.concept}"
            )

        # -----------------------------
        # Test 3: Unknown concept
        # -----------------------------

        print("\n=== UNKNOWN CONCEPT ===")

        result = retriever.retrieve(
            "SomethingThatDoesNotExist"
        )

        print(f"Found: {result.found}")
        print(f"Source: {result.source}")


if __name__ == "__main__":
    main()