from app.db.models.assessment import AssessmentAttempt

from app.services.learner.evidence import (
    LearnerEvidenceService,
)


class AssessmentEvidenceService:

    def __init__(self, db):
        self.evidence_service = (
            LearnerEvidenceService(db)
        )

    def record_attempt(
        self,
        attempt: AssessmentAttempt,
        skill_id: str,
    ):

        return self.evidence_service.record(
            learner_id=attempt.learner_id,
            skill_id=skill_id,
            evidence_type="assessment",
            score=attempt.score,
            source_id=attempt.id,
            metadata={
                "assessment_id": attempt.assessment_id,
                "correct_answers": (
                    attempt.correct_answers
                ),
                "total_questions": (
                    attempt.total_questions
                ),
            },
        )