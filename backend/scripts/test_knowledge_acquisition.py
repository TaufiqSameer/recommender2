from app.db.database import SessionLocal

from app.services.knowledge.acquisition import (
    KnowledgeAcquisitionService,
)

from app.services.knowledge.repository import (
    KnowledgeRepository,
)


def main():

    with SessionLocal() as db:

        repository = KnowledgeRepository(db)

        service = KnowledgeAcquisitionService(db)

        # =====================================
        # TEST 1: VALID CANDIDATE
        # =====================================

        print("=== VALID CANDIDATE ===")

        valid = repository.create_candidate(
            concept="GraphQL",
            domain="backend",
            description=(
                "A query language and runtime "
                "for APIs."
            ),
            proposed_relationships=[
                {
                    "type": "related_to",
                    "target": "rest",
                }
            ],
            sources=[
                "https://graphql.org/"
            ],
            confidence=0.95,
        )

        result = service.validate_candidate(
            valid.id
        )

        print(f"Concept: {result.concept}")
        print(
            f"Status: "
            f"{result.verification_status}"
        )
        print(
            f"Retries: "
            f"{result.retry_count}"
        )

        # =====================================
        # TEST 2: INVALID CANDIDATE
        # =====================================

        print("\n=== INVALID CANDIDATE ===")

        invalid = repository.create_candidate(
            concept="",
            domain="backend",
            description=None,
            proposed_relationships=[],
            sources=[],
            confidence=0.20,
        )

        # First attempt
        result = service.validate_candidate(
            invalid.id
        )

        print(
            f"After attempt 1: "
            f"retries={result.retry_count}, "
            f"status={result.verification_status}"
        )

        # Second attempt
        result = service.validate_candidate(
            invalid.id
        )

        print(
            f"After attempt 2: "
            f"retries={result.retry_count}, "
            f"status={result.verification_status}"
        )

        print(
            f"Reason: "
            f"{result.rejection_reason}"
        )


if __name__ == "__main__":
    main()