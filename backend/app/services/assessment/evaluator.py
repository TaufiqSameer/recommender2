from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
)


@dataclass
class EvaluatedAnswer:
    question_id: str
    answer: str
    correct: bool
    score: float


@dataclass
class EvaluationResult:
    attempt: AssessmentAttempt
    answers: list[EvaluatedAnswer]


class AssessmentEvaluator:

    def __init__(self, db: Session):
        self.db = db

    def evaluate(
        self,
        *,
        attempt_id: str,
        learner_id: str,
        assessment_id: str,
        learner_answers: dict[str, str],
    ) -> EvaluationResult:

        # -----------------------------------------
        # 1. Load the assessment questions
        # -----------------------------------------

        questions = (
            self.db.query(AssessmentQuestion)
            .filter(
                AssessmentQuestion.assessment_id
                == assessment_id
            )
            .all()
        )

        if not questions:
            raise ValueError(
                "Assessment contains no questions."
            )

        # -----------------------------------------
        # 2. Prevent accidental duplicate attempts
        # -----------------------------------------

        existing_attempt = (
            self.db.query(AssessmentAttempt)
            .filter(
                AssessmentAttempt.id == attempt_id
            )
            .first()
        )

        if existing_attempt:
            raise ValueError(
                f"Assessment attempt "
                f"'{attempt_id}' already exists."
            )

        # -----------------------------------------
        # 3. Create attempt
        # -----------------------------------------

        attempt = AssessmentAttempt(
            id=attempt_id,
            learner_id=learner_id,
            assessment_id=assessment_id,
            total_questions=len(questions),
            correct_answers=0,
            score=0.0,
        )

        self.db.add(attempt)
        self.db.flush()

        evaluated_answers: list[EvaluatedAnswer] = []

        correct_count = 0

        # -----------------------------------------
        # 4. Evaluate every question
        # -----------------------------------------

        for question in questions:

            if question.id not in learner_answers:
                raise ValueError(
                    f"Missing answer for "
                    f"question '{question.id}'."
                )

            learner_answer = learner_answers[
                question.id
            ]

            correct = self._is_correct(
                question,
                learner_answer,
            )

            score = 1.0 if correct else 0.0

            if correct:
                correct_count += 1

            evaluated = EvaluatedAnswer(
                question_id=question.id,
                answer=learner_answer,
                correct=correct,
                score=score,
            )

            evaluated_answers.append(
                evaluated
            )

            # -------------------------------------
            # Store individual answer
            # -------------------------------------

            answer_record = AssessmentAnswer(
                id=f"{attempt_id}-{question.id}",
                attempt_id=attempt_id,
                question_id=question.id,
                answer=learner_answer,
                correct=correct,
                score=score,
            )

            self.db.add(answer_record)

        # -----------------------------------------
        # 5. Calculate overall result
        # -----------------------------------------

        total_questions = len(questions)

        overall_score = (
            correct_count / total_questions
        )

        attempt.correct_answers = correct_count
        attempt.total_questions = total_questions
        attempt.score = overall_score
        attempt.completed_at = datetime.utcnow()

        # -----------------------------------------
        # 6. Commit everything together
        # -----------------------------------------

        try:

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise

        return EvaluationResult(
            attempt=attempt,
            answers=evaluated_answers,
        )

    # =================================================
    # Answer evaluation
    # =================================================

    @staticmethod
    def _is_correct(
        question: AssessmentQuestion,
        learner_answer: str,
    ) -> bool:

        expected = (
            question.correct_answer
            .strip()
            .lower()
        )

        actual = (
            learner_answer
            .strip()
            .lower()
        )

        # -----------------------------------------
        # Multiple choice / true false
        # -----------------------------------------

        if question.question_type in {
            "multiple_choice",
            "true_false",
        }:

            return actual == expected

        # -----------------------------------------
        # Short answer
        # -----------------------------------------

        if question.question_type == "short_answer":

            return AssessmentEvaluator._normalize(
                actual
            ) == AssessmentEvaluator._normalize(
                expected
            )

        raise ValueError(
            f"Unsupported question type: "
            f"{question.question_type}"
        )

    @staticmethod
    def _normalize(value: str) -> str:

        return " ".join(
            value.strip().lower().split()
        )