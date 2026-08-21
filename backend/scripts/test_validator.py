from app.services.knowledge.validator import (
    KnowledgeValidator,
)


def main():

    validator = KnowledgeValidator()

    print("=== VALID CANDIDATE ===")

    result = validator.validate(
        concept="GraphQL",
        description=(
            "A query language and runtime "
            "for APIs."
        ),
        relationships=[
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

    print(f"Accepted: {result.accepted}")
    print(f"Confidence: {result.confidence}")
    print(f"Reasons: {result.reasons}")

    print("\n=== INVALID CANDIDATE ===")

    result = validator.validate(
        concept="",
        description=None,
        relationships=[],
        sources=[],
        confidence=0.30,
    )

    print(f"Accepted: {result.accepted}")
    print(f"Confidence: {result.confidence}")
    print("Reasons:")

    for reason in result.reasons:
        print(f"- {reason}")


if __name__ == "__main__":
    main()