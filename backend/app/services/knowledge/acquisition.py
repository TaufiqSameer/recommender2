from app.domain.verification import VerificationStatus

from app.services.knowledge.repository import (
    KnowledgeRepository,
)

from app.services.knowledge.retriever import (
    KnowledgeRetriever,
)

from app.services.knowledge.researcher import (
    KnowledgeResearcher,
)

from app.services.knowledge.validator import (
    KnowledgeValidator,
)


class KnowledgeAcquisitionService:

    MAX_RETRIES = 2

    def __init__(self, db):

        self.repository = KnowledgeRepository(db)
        self.retriever = KnowledgeRetriever(db)
        self.researcher = KnowledgeResearcher()
        self.validator = KnowledgeValidator()

    def acquire(
        self,
        concept: str,
        domain: str | None = None,
    ):

        # ---------------------------------
        # 1. Search existing knowledge
        # ---------------------------------

        existing = self.retriever.retrieve(
            concept
        )

        if existing.found:
            return {
                "status": "found",
                "source": existing.source,
                "skill": existing.skill,
                "candidate": existing.candidate,
            }

        # ---------------------------------
        # 2. Knowledge not found
        # ---------------------------------

        for attempt in range(
            self.MAX_RETRIES + 1
        ):

            print(
                f"Research attempt "
                f"{attempt + 1}/"
                f"{self.MAX_RETRIES + 1}"
            )

            # -----------------------------
            # Gemini research
            # -----------------------------

            research = self.researcher.research(
                concept=concept,
                domain=domain,
            )

            # -----------------------------
            # Create candidate
            # -----------------------------

            candidate = (
                self.repository.create_candidate(
                    concept=research.concept,
                    domain=research.domain,
                    description=research.description,
                    proposed_relationships=[
                        relationship.model_dump()
                        for relationship
                        in research.proposed_relationships
                    ],
                    sources=research.sources,
                    confidence=research.confidence,
                )
            )

            # -----------------------------
            # Validate candidate
            # -----------------------------

            result = self.validator.validate(
                concept=candidate.concept,
                description=candidate.description,
                relationships=(
                    candidate.proposed_relationships
                ),
                sources=candidate.sources,
                confidence=candidate.confidence,
            )

            # -----------------------------
            # ACCEPT
            # -----------------------------

            if result.accepted:

                verified = (
                    self.repository.update_status(
                        candidate,
                        VerificationStatus.VERIFIED.value,
                    )
                )

                return {
                    "status": "acquired",
                    "source": "gemini",
                    "candidate": verified,
                    "attempt": attempt + 1,
                }

            # -----------------------------
            # REJECT
            # -----------------------------

            candidate.retry_count += 1

            candidate.rejection_reason = (
                "; ".join(result.reasons)
            )

            # If this wasn't the last attempt,
            # save and ask Gemini again.
            if attempt < self.MAX_RETRIES:

                self.repository.save(candidate)

                continue

            # -----------------------------
            # RETRIES EXHAUSTED
            # -----------------------------

            pending = (
                self.repository.update_status(
                    candidate,
                    VerificationStatus.PENDING_REVIEW.value,
                    rejection_reason=(
                        "; ".join(result.reasons)
                    ),
                )
            )

            return {
                "status": "pending_review",
                "source": "gemini",
                "candidate": pending,
                "attempt": attempt + 1,
                "reasons": result.reasons,
            }

        raise RuntimeError(
            "Knowledge acquisition failed."
        )