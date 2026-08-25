from app.ai.chains.learning_activity import (
    LearningActivityChain,
)


def main():

    chain = LearningActivityChain()

    activity = chain.invoke(
        skill="FastAPI",
        description=(
            "A modern Python web framework "
            "for building APIs."
        ),
        skill_difficulty="intermediate",
        learning_objectives=[
            "Build REST API endpoints",
            "Validate request data",
            "Handle HTTP responses",
        ],
        mastery=0.0,
        theta=0.0,
        confidence=0.0,
        mastered_prerequisites=[
            "API Design & Best Practices",
            "PostgreSQL",
        ],
        unmet_prerequisites=[],
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "GEMINI LEARNING ACTIVITY"
    )

    print(
        "=" * 60
    )

    print(
        f"\nTitle:\n"
        f"{activity.title}"
    )

    print(
        f"\nType:\n"
        f"{activity.activity_type}"
    )

    print(
        f"\nObjective:\n"
        f"{activity.objective}"
    )

    print(
        f"\nDifficulty:\n"
        f"{activity.difficulty}"
    )

    print(
        f"\nInstructions:\n"
        f"{activity.instructions}"
    )

    print(
        "\nHints:"
    )

    for index, hint in enumerate(
        activity.hints,
        start=1,
    ):

        print(
            f"  {index}. {hint}"
        )

    print(
        "\n"
        + "=" * 60
    )


if __name__ == "__main__":
    main()