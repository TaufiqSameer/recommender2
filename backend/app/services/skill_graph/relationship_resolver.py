from sqlalchemy.orm import Session

from app.db.models import SkillNode

from app.services.knowledge.acquisition import (
    KnowledgeAcquisitionService,
)


class RelationshipResolver:

    def __init__(self, db: Session):

        self.db = db

        self.acquisition = (
            KnowledgeAcquisitionService(db)
        )

    def resolve_prerequisites(
        self,
        relationships: list[dict],
        resolving: set[str] | None = None,
    ) -> list[SkillNode]:

        if resolving is None:
            resolving = set()

        resolved: list[SkillNode] = []

        for relationship in relationships or []:

            # We currently only treat
            # "requires" as a graph prerequisite.
            if relationship.get("type") != "requires":
                continue

            target = relationship.get("target")

            if not target:
                continue

            target = target.strip()

            if not target:
                continue

            # -----------------------------------------
            # Prevent recursive dependency cycles
            # -----------------------------------------

            target_key = target.lower()

            if target_key in resolving:
                raise ValueError(
                    "Recursive prerequisite cycle "
                    f"detected involving '{target}'."
                )

            # -----------------------------------------
            # Check if prerequisite already exists
            # -----------------------------------------

            skill = (
                self.db.query(SkillNode)
                .filter(
                    SkillNode.label.ilike(
                        target
                    )
                )
                .first()
            )

            if skill is not None:

                resolved.append(skill)

                continue

            # -----------------------------------------
            # Prerequisite doesn't exist.
            #
            # Ask the knowledge acquisition layer
            # to discover it.
            # -----------------------------------------

            next_resolving = set(resolving)

            next_resolving.add(
                target_key
            )

            result = self.acquisition.acquire(
                concept=target,
                domain=None,
            )

            # -----------------------------------------
            # Acquisition failed to produce trusted
            # knowledge.
            # -----------------------------------------

            if result["status"] == "pending_review":

                raise ValueError(
                    f"Prerequisite '{target}' "
                    "could not be verified."
                )

            # -----------------------------------------
            # We acquired/found the prerequisite.
            # -----------------------------------------

            candidate = result.get(
                "candidate"
            )

            if candidate is not None:

                # At this stage the candidate has
                # been verified, but it may not yet
                # exist in SkillNode.
                #
                # We deliberately DO NOT insert it
                # here. Graph integration remains
                # responsible for graph mutations.

                skill = (
                    self.db.query(SkillNode)
                    .filter(
                        SkillNode.label.ilike(
                            target
                        )
                    )
                    .first()
                )

                if skill is None:

                    raise ValueError(
                        f"Prerequisite '{target}' "
                        "was verified but has not "
                        "yet been integrated into "
                        "the skill graph."
                    )

                resolved.append(skill)

        return resolved