from app.db.database import SessionLocal

from app.db.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
)

from app.services.assessment.evaluator import (
    AssessmentEvaluator,
)


def main():

    db = SessionLocal()

    try:

        assessment_id = "http-baseline-001"
        learner_id = "learner-001"
        attempt_id = "http-attempt-001"

        # -----------------------------------------
        # Get questions from the database
        # -----------------------------------------

        questions = (
            db.query(AssessmentQuestion)
            .filter(
                AssessmentQuestion.assessment_id
                == assessment_id
            )
            .order_by(
                AssessmentQuestion.id
            )
            .all()
        )

        if not questions:
            raise RuntimeError(
                "No assessment questions found. "
                "Run test_assessment_service first."
            )

        print("=== QUESTIONS ===")

        for question in questions:

            print(
                f"{question.id}: "
                f"{question.correct_answer}"
            )

        # -----------------------------------------
        # Simulate learner answers
        # -----------------------------------------

        learner_answers = {
            questions[0].id:
                questions[0].correct_answer,

            questions[1].id:
                questions[1].correct_answer,

            # Deliberately wrong.
            questions[2].id:
                "WRONG ANSWER",

            questions[3].id:
                questions[3].correct_answer,

            questions[4].id:
                questions[4].correct_answer,
        }

        # -----------------------------------------
        # Evaluate
        # -----------------------------------------

        evaluator = AssessmentEvaluator(db)

        result = evaluator.evaluate(
            attempt_id=attempt_id,
            learner_id=learner_id,
            assessment_id=assessment_id,
            learner_answers=learner_answers,
        )

        # -----------------------------------------
        # Display result
        # -----------------------------------------

        print("\n=== EVALUATION RESULT ===")

        for answer in result.answers:

            print(
                f"{answer.question_id}: "
                f"{'CORRECT' if answer.correct else 'WRONG'} "
                f"score={answer.score}"
            )

        print("\n=== ATTEMPT ===")

        print(
            f"Attempt: "
            f"{result.attempt.id}"
        )

        print(
            f"Correct: "
            f"{result.attempt.correct_answers}/"
            f"{result.attempt.total_questions}"
        )

        print(
            f"Score: "
            f"{result.attempt.score:.2f}"
        )

        # -----------------------------------------
        # Verify database records
        # -----------------------------------------

        stored_attempt = (
            db.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.id
                == attempt_id
            )
            .first()
        )

        stored_answers = (
            db.query(AssessmentAnswer)
            .filter(
                AssessmentAnswer.attempt_id
                == attempt_id
            )
            .all()
        )

        print(
            "\n=== DATABASE VERIFICATION ==="
        )

        print(
            f"Attempt found: "
            f"{stored_attempt is not None}"
        )

        print(
            f"Answers found: "
            f"{len(stored_answers)}"
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()