from app.services.knowledge.researcher import (
    KnowledgeResearcher,
)


def main():

    researcher = KnowledgeResearcher()

    result = researcher.research(
        concept="Actix Web",
        domain="backend",
    )

    print("=== RESEARCH RESULT ===")

    print(f"Concept: {result.concept}")
    print(f"Domain: {result.domain}")
    print(f"Description: {result.description}")
    print(f"Confidence: {result.confidence}")

    print("\nRelationships:")

    for relationship in result.proposed_relationships:
        print(f"- {relationship}")

    print("\nSources:")

    for source in result.sources:
        print(f"- {source}")


if __name__ == "__main__":
    main()