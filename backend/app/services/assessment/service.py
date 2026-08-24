from sqlalchemy.orm import Session

from app.db.models.assessment import (
    Assessment,
    AssessmentQuestion,
)

from app.services.assessment.generator import (
    GeneratedAssessment,
)


class AssessmentService:

    def __init__(self, db: Session):
        self.db = db

    def save_generated_assessment(
        self,
        *,
        assessment_id: str,
        skill_id: str,
        generated: GeneratedAssessment,
    ) -> Assessment:

        # -----------------------------------------
        # 1. Create the assessment
        # -----------------------------------------

        assessment = Assessment(
            id=assessment_id,
            skill_id=skill_id,
            title=generated.title,
            description=generated.description,
            difficulty=self._calculate_assessment_difficulty(
                generated
            ),
            generation_source="llm",
        )

        self.db.add(assessment)

        # -----------------------------------------
        # 2. Create the questions
        # -----------------------------------------

        for index, generated_question in enumerate(
            generated.questions,
            start=1,
        ):

            question = AssessmentQuestion(
                id=f"{assessment_id}-q{index}",
                assessment_id=assessment_id,
                skill_id=skill_id,
                question=generated_question.question,
                question_type=(
                    generated_question.question_type
                ),
                question_data={
                    "options": generated_question.options,
                },
                correct_answer=(
                    generated_question.correct_answer
                ),
                explanation=(
                    generated_question.explanation
                ),
                difficulty=(
                    generated_question.difficulty
                ),
                discrimination=1.0,
            )

            self.db.add(question)

        # -----------------------------------------
        # 3. Commit everything together
        # -----------------------------------------

        try:

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise

        # -----------------------------------------
        # 4. Return the saved assessment
        # -----------------------------------------

        return assessment

    @staticmethod
    def _calculate_assessment_difficulty(
        generated: GeneratedAssessment,
    ) -> float:

        if not generated.questions:
            return 1.0

        total = sum(
            question.difficulty
            for question
            in generated.questions
        )

        return total / len(
            generated.questions
        )