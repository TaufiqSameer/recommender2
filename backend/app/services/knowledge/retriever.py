from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import (
    KnowledgeCandidate,
    SkillNode,
)
from app.domain.verification import (
    VerificationStatus,
)


@dataclass
class KnowledgeResult:
    found: bool
    source: str | None
    skill: SkillNode | None
    candidate: KnowledgeCandidate | None


class KnowledgeRetriever:

    def __init__(self, db: Session):
        self.db = db

    def retrieve(
        self,
        concept: str,
    ) -> KnowledgeResult:

        concept = concept.strip()

        if not concept:
            return KnowledgeResult(
                found=False,
                source=None,
                skill=None,
                candidate=None,
            )



        skill = (
            self.db.query(SkillNode)
            .filter(
                SkillNode.label.ilike(
                    concept
                )
            )
            .first()
        )

        if skill is not None:

            return KnowledgeResult(
                found=True,
                source="skill_graph",
                skill=skill,
                candidate=None,
            )

        candidate = (
            self.db.query(KnowledgeCandidate)
            .filter(
                KnowledgeCandidate.concept.ilike(
                    concept
                ),
                KnowledgeCandidate.verification_status
                == VerificationStatus.VERIFIED.value,
            )
            .first()
        )

        if candidate is not None:

            return KnowledgeResult(
                found=True,
                source="knowledge_candidate",
                skill=None,
                candidate=candidate,
            )


        return KnowledgeResult(
            found=False,
            source=None,
            skill=None,
            candidate=None,
        )