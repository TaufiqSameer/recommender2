from app.domain.verification import VerificationStatus

from app.services.knowledge.repository import (
    KnowledgeRepository,
)

from app.services.knowledge.validator import (
    KnowledgeValidator,
)
from app.domain.verification import VerificationStatus


class KnowledgeAcquisitionService:

    MAX_RETRIES = 2

    def __init__(self, db):

        self.repository = KnowledgeRepository(db)
        self.validator = KnowledgeValidator()

    def validate_candidate(
        self,
        candidate_id: int,
    ):

        candidate = self.repository.get_candidate(
            candidate_id
        )

        if candidate is None:
            raise ValueError(
                f"Knowledge candidate "
                f"{candidate_id} not found."
            )

        result = self.validator.validate(
            concept=candidate.concept,
            description=candidate.description,
            relationships=(
                candidate.proposed_relationships
            ),
            sources=candidate.sources,
            confidence=candidate.confidence,
        )

        if result.accepted:

            return self.repository.update_status(
                candidate,
                VerificationStatus.VERIFIED.value,
            )

        candidate.retry_count += 1

        if candidate.retry_count >= self.MAX_RETRIES:

            return self.repository.update_status(
                candidate,
                VerificationStatus.PENDING_REVIEW.value,
                rejection_reason="; ".join(
                    result.reasons
                ),
            )

        self.db_commit(candidate)

        return candidate

    def db_commit(self, candidate):

        self.repository.db.commit()
        self.repository.db.refresh(candidate)