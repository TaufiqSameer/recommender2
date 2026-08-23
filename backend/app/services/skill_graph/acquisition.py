from sqlalchemy.orm import Session

from app.db.models import (
    KnowledgeCandidate,
    SkillNode,
)

from app.services.knowledge.acquisition import (
    KnowledgeAcquisitionService,
)

from app.services.skill_graph.integrator import (
    KnowledgeGraphIntegrator,
)


class KnowledgeGraphAcquisitionService:

    MAX_DEPTH = 3

    def __init__(self, db: Session):

        self.db = db

        self.knowledge_acquisition = (
            KnowledgeAcquisitionService(db)
        )

        self.integrator = (
            KnowledgeGraphIntegrator(db)
        )

    def acquire_skill(
        self,
        concept: str,
        domain: str | None = None,
    ) -> SkillNode:

        resolving: set[str] = set()

        return self._acquire_recursive(
            concept=concept,
            domain=domain,
            resolving=resolving,
            depth=0,
        )

    def _acquire_recursive(
        self,
        concept: str,
        domain: str | None,
        resolving: set[str],
        depth: int,
    ) -> SkillNode:

        # -----------------------------------------
        # 1. Protect against excessive recursion
        # -----------------------------------------

        if depth > self.MAX_DEPTH:

            raise ValueError(
                "Maximum prerequisite acquisition "
                f"depth ({self.MAX_DEPTH}) exceeded "
                f"while resolving '{concept}'."
            )

        concept_key = concept.strip().lower()

        if not concept_key:

            raise ValueError(
                "Skill concept cannot be empty."
            )

        # -----------------------------------------
        # 2. Detect recursive dependency cycles
        # -----------------------------------------

        if concept_key in resolving:

            chain = " -> ".join(
                list(resolving) + [concept]
            )

            raise ValueError(
                "Recursive prerequisite cycle "
                f"detected: {chain}"
            )

        # -----------------------------------------
        # 3. If skill already exists, we're done
        # -----------------------------------------

        existing = (
            self.db.query(SkillNode)
            .filter(
                SkillNode.label.ilike(
                    concept
                )
            )
            .first()
        )

        if existing is not None:

            return existing

        # -----------------------------------------
        # 4. Mark this concept as being resolved
        # -----------------------------------------

        current_resolving = set(resolving)

        current_resolving.add(
            concept_key
        )

        # -----------------------------------------
        # 5. Acquire knowledge
        #
        # Retriever:
        #     FOUND → existing candidate/skill
        #
        #     MISS → Gemini → validation
        # -----------------------------------------

        result = (
            self.knowledge_acquisition.acquire(
                concept=concept,
                domain=domain,
            )
        )

        # -----------------------------------------
        # 6. Acquisition could not verify it
        # -----------------------------------------

        if result["status"] == "pending_review":

            raise ValueError(
                f"Knowledge for '{concept}' "
                "could not be verified."
            )

        # -----------------------------------------
        # 7. Existing SkillNode
        # -----------------------------------------

        if result.get("skill") is not None:

            return result["skill"]

        # -----------------------------------------
        # 8. Get the verified candidate
        # -----------------------------------------

        candidate = result.get(
            "candidate"
        )

        if candidate is None:

            raise ValueError(
                f"No usable knowledge returned "
                f"for '{concept}'."
            )

        if not isinstance(
            candidate,
            KnowledgeCandidate,
        ):

            raise TypeError(
                "Expected KnowledgeCandidate, "
                f"got {type(candidate).__name__}."
            )

        # -----------------------------------------
        # 9. Recursively resolve prerequisites
        # -----------------------------------------

        self._resolve_prerequisites(
            candidate=candidate,
            resolving=current_resolving,
            depth=depth,
        )

        # -----------------------------------------
        # 10. All prerequisites now exist.
        #
        # Integrate the candidate into the graph.
        # -----------------------------------------

        skill = self.integrator.integrate(
            candidate.id
        )

        return skill

    def _resolve_prerequisites(
        self,
        candidate: KnowledgeCandidate,
        resolving: set[str],
        depth: int,
    ):

        for relationship in (
            candidate.proposed_relationships
            or []
        ):

            # Only "requires" currently creates
            # prerequisite edges.
            if relationship.get("type") != "requires":
                continue

            if relationship.get("strength") != "hard":
                continue

            target = relationship.get(
                "target"
            )

            if not target:
                continue

            target = target.strip()

            if not target:
                continue

            # -------------------------------------
            # Check whether prerequisite exists
            # -------------------------------------

            existing = (
                self.db.query(SkillNode)
                .filter(
                    SkillNode.label.ilike(
                        target
                    )
                )
                .first()
            )

            if existing is not None:
                continue

            # -------------------------------------
            # Missing prerequisite:
            # recursively acquire it.
            # -------------------------------------

            self._acquire_recursive(
                concept=target,
                domain=candidate.domain,
                resolving=resolving,
                depth=depth + 1,
            )