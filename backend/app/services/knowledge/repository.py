from sqlalchemy.orm import Session

from app.db.models import KnowledgeCandidate
from app.domain.verification import VerificationStatus

class KnowledgeRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_candidate(
        self,
        concept: str,
        domain: str | None,
        description: str | None,
        proposed_relationships: list,
        sources: list,
        confidence: float,
    ) -> KnowledgeCandidate:

        candidate = KnowledgeCandidate(
            concept=concept,
            domain=domain,
            description=description,
            proposed_relationships=proposed_relationships,
            sources=sources,
            confidence=confidence,
        )

        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)

        return candidate

    def get_candidate(
        self,
        candidate_id: int,
    ) -> KnowledgeCandidate | None:

        return (
            self.db.query(KnowledgeCandidate)
            .filter(
                KnowledgeCandidate.id == candidate_id
            )
            .first()
        )

    def get_candidates_by_concept(
        self,
        concept: str,
    ) -> list[KnowledgeCandidate]:

        return (
            self.db.query(KnowledgeCandidate)
            .filter(
                KnowledgeCandidate.concept.ilike(
                    concept
                )
            )
            .all()
        )

    def get_pending_candidates(
        self,
    ) -> list[KnowledgeCandidate]:

        return (
            self.db.query(KnowledgeCandidate)
            .filter(
                KnowledgeCandidate.verification_status
                == VerificationStatus.PENDING_REVIEW.value
            )
            .all()
        )

    def update_status(
        self,
        candidate: KnowledgeCandidate,
        status: str,
        rejection_reason: str | None = None,
    ) -> KnowledgeCandidate:

        candidate.verification_status = status
        candidate.rejection_reason = rejection_reason

        self.db.commit()
        self.db.refresh(candidate)

        return candidate

    def save(
        self,
        candidate: KnowledgeCandidate,
    ) -> KnowledgeCandidate:

        self.db.commit()
        self.db.refresh(candidate)

        return candidate

    def delete_candidate(
        self,
        candidate: KnowledgeCandidate,
    ) -> None:

        self.db.delete(candidate)
        self.db.commit()