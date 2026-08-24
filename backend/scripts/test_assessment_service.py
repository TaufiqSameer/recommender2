from app.db.database import SessionLocal
from app.services.assessment.generator import (
    AssessmentGenerator,
)
from app.services.assessment.service import (
    AssessmentService,
)


def main():

    db = SessionLocal()

    try:

        # -----------------------------------------
        # 1. Generate assessment with Gemini
        # -----------------------------------------

        generator = AssessmentGenerator()

        generated = generator.generate(
            skill_name="HTTP",
            skill_description=(
                "The Hypertext Transfer Protocol and "
                "its request-response model, methods, "
                "status codes, headers, and semantics."
            ),
            difficulty=2.0,
            num_questions=5,
        )

        # -----------------------------------------
        # 2. Save assessment
        # -----------------------------------------

        service = AssessmentService(db)

        assessment = (
            service.save_generated_assessment(
                assessment_id="http-baseline-001",
                skill_id="http",
                generated=generated,
            )
        )

        print("=== ASSESSMENT SAVED ===")

        print(
            f"ID: {assessment.id}"
        )

        print(
            f"Skill: {assessment.skill_id}"
        )

        print(
            f"Title: {assessment.title}"
        )

        # -----------------------------------------
        # 3. Verify database contents
        # -----------------------------------------

        from app.db.models.assessment import (
            AssessmentQuestion,
        )

        questions = (
            db.query(AssessmentQuestion)
            .filter(
                AssessmentQuestion.assessment_id
                == assessment.id
            )
            .all()
        )

        print(
            "\n=== DATABASE VERIFICATION ==="
        )

        print(
            f"Assessment found: "
            f"{assessment is not None}"
        )

        print(
            f"Questions found: "
            f"{len(questions)}"
        )

        for index, question in enumerate(
            questions,
            start=1,
        ):

            print(
                f"\n{index}. "
                f"{question.question}"
            )

            print(
                f"   Type: "
                f"{question.question_type}"
            )

            print(
                f"   Difficulty: "
                f"{question.difficulty}"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()