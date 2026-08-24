from app.services.assessment.generator import (
    AssessmentGenerator,
)


def main():

    generator = AssessmentGenerator()

    assessment = generator.generate(
        skill_name="HTTP",
        skill_description=(
            "The Hypertext Transfer Protocol and "
            "its request-response model, methods, "
            "status codes, headers, and HTTP semantics."
        ),
        difficulty=2.0,
        num_questions=5,
    )

    print("=== GENERATED ASSESSMENT ===")

    print(f"Title: {assessment.title}")
    print(f"Description: {assessment.description}")

    print(
        f"\nQuestions: "
        f"{len(assessment.questions)}"
    )

    for index, question in enumerate(
        assessment.questions,
        start=1,
    ):

        print(f"\n{index}. {question.question}")

        print(
            f"   Type: "
            f"{question.question_type}"
        )

        print(
            f"   Difficulty: "
            f"{question.difficulty}"
        )

        if question.options:

            print("   Options:")

            for option in question.options:
                print(f"      - {option}")

        print(
            f"   Correct: "
            f"{question.correct_answer}"
        )

        print(
            f"   Explanation: "
            f"{question.explanation}"
        )


if __name__ == "__main__":
    main()