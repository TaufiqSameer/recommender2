from app.ai.chains.goal_understanding import (
    GoalUnderstandingChain,
)


def main() -> None:

    message = """
    I want to become a backend engineer.
    I already know Python pretty well and I have
    some experience with SQL.

    I can study around 6 hours per week.

    I prefer building projects instead of watching
    long video courses.

    I'm particularly interested in APIs and FastAPI.
    """

    chain = GoalUnderstandingChain()

    intent = chain.invoke(message)

    print("\nLearner Intent:\n")

    print(f"Goal: {intent.goal}")

    print(
        f"Known skills: "
        f"{intent.known_skills}"
    )

    print(
        f"Weekly hours: "
        f"{intent.weekly_hours}"
    )

    print(
        f"Learning style: "
        f"{intent.learning_style}"
    )

    print(
        f"Focus areas: "
        f"{intent.focus_areas}"
    )


if __name__ == "__main__":
    main()