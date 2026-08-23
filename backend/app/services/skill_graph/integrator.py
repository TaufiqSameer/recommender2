from sqlalchemy.orm import Session

from app.db.models import (
    KnowledgeCandidate,
    SkillEdge,
    SkillNode,
)

from app.domain.verification import (
    VerificationStatus,
)

from app.services.skill_graph.validation import (
    validate_graph,
    SkillGraphValidationError,
)


class KnowledgeGraphIntegrator:

    def __init__(self, db: Session):
        self.db = db

    def integrate(
        self,
        candidate_id: int,
    ) -> SkillNode:

        candidate = (
            self.db.query(KnowledgeCandidate)
            .filter(
                KnowledgeCandidate.id
                == candidate_id
            )
            .first()
        )

        if candidate is None:
            raise ValueError(
                f"Knowledge candidate "
                f"{candidate_id} not found."
            )

        if (
            candidate.verification_status
            != VerificationStatus.VERIFIED.value
        ):
            raise ValueError(
                "Only verified knowledge "
                "can enter the skill graph."
            )

        existing = (
            self.db.query(SkillNode)
            .filter(
                SkillNode.label.ilike(
                    candidate.concept
                )
            )
            .first()
        )

        if existing is not None:
            return existing

        return self._integrate_candidate(
            candidate
        )

    def _integrate_candidate(
        self,
        candidate: KnowledgeCandidate,
    ) -> SkillNode:

        skill = SkillNode(
            id=self._make_skill_id(
                candidate.concept
            ),
            domain=(
                candidate.domain
                or "unknown"
            ),
            label=candidate.concept,
            description=(
                candidate.description
                or ""
            ),
            difficulty=3.0,
            learning_objectives=[],
        )

        self.db.add(skill)
        self.db.flush()

        for relationship in (
            candidate.proposed_relationships
            or []
        ):

            if relationship.get("type") != "requires":
                continue

            if relationship.get("strength") != "hard":
                continue

            target = relationship.get("target")

            if not target:
                continue

            prerequisite = (
                self.db.query(SkillNode)
                .filter(
                    SkillNode.label.ilike(
                        target
                    )
                )
                .first()
            )

            if prerequisite is None:

                self.db.rollback()

                raise ValueError(
                    f"Prerequisite skill "
                    f"'{target}' does not exist "
                    "in the skill graph."
                )

            if prerequisite.id == skill.id:

                self.db.rollback()

                raise ValueError(
                    "A skill cannot depend "
                    "on itself."
                )

            existing_edge = (
                self.db.query(SkillEdge)
                .filter(
                    SkillEdge.prerequisite_id
                    == prerequisite.id,
                    SkillEdge.dependent_id
                    == skill.id,
                )
                .first()
            )

            if existing_edge is not None:
                continue

            self.db.add(
                SkillEdge(
                    prerequisite_id=(
                        prerequisite.id
                    ),
                    dependent_id=skill.id,
                )
            )

        self.db.flush()

        self._validate_graph()

        self.db.commit()
        self.db.refresh(skill)

        return skill

    def _validate_graph(self):

        skills = (
            self.db.query(SkillNode)
            .all()
        )

        edges = (
            self.db.query(SkillEdge)
            .all()
        )

        try:

            validate_graph(
                skills=skills,
                edges=edges,
            )

        except SkillGraphValidationError:

            self.db.rollback()

            raise

    @staticmethod
    def _make_skill_id(
        concept: str,
    ) -> str:

        return (
            concept.strip()
            .lower()
            .replace(" ", "-")
            .replace("/", "-")
            .replace("_", "-")
        )