from app.db.database import SessionLocal

from app.services.knowledge.repository import (
    KnowledgeRepository,
)


def main():

    with SessionLocal() as db:

        repository = KnowledgeRepository(db)

        candidate = repository.create_candidate(
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
            confidence=0.92,
        )

        print("Candidate created:")
        print(f"ID: {candidate.id}")
        print(f"Concept: {candidate.concept}")
        print(
            f"Status: "
            f"{candidate.verification_status}"
        )

        fetched = repository.get_candidate(
            candidate.id
        )

        print("\nFetched candidate:")
        print(fetched.concept)

        candidates = (
            repository.get_candidates_by_concept(
                "GraphQL"
            )
        )

        print(
            f"\nCandidates found: "
            f"{len(candidates)}"
        )


if __name__ == "__main__":
    main()