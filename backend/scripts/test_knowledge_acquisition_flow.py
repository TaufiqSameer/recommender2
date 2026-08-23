from app.db.database import SessionLocal

from app.services.knowledge.acquisition import (
    KnowledgeAcquisitionService,
)


def main():

    with SessionLocal() as db:

        service = KnowledgeAcquisitionService(db)

        # =====================================
        # TEST 1
        # Existing knowledge
        # =====================================

        print("\n=== EXISTING KNOWLEDGE ===")

        result = service.acquire(
            concept="FastAPI",
            domain="backend",
        )

        print(
            f"Status: {result['status']}"
        )

        print(
            f"Source: {result['source']}"
        )

        # =====================================
        # TEST 2
        # Unknown knowledge
        # =====================================

        print("\n=== UNKNOWN KNOWLEDGE ===")

        result = service.acquire(
            concept="Actix Web",
            domain="backend",
        )

        print(
            f"Status: {result['status']}"
        )

        print(
            f"Source: {result['source']}"
        )

        candidate = result.get(
            "candidate"
        )

        if candidate:

            print(
                f"Concept: "
                f"{candidate.concept}"
            )

            print(
                f"Verification: "
                f"{candidate.verification_status}"
            )

            print(
                f"Confidence: "
                f"{candidate.confidence}"
            )

            print(
                f"Retries: "
                f"{candidate.retry_count}"
            )


if __name__ == "__main__":
    main()