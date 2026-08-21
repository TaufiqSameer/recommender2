from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SkillEdge, SkillNode


class SkillGraphService:

    def __init__(self, db: Session):
        self.db = db

    def get_skill(
        self,
        skill_id: str,
    ) -> SkillNode | None:

        return self.db.get(
            SkillNode,
            skill_id,
        )

    def get_prerequisites(
        self,
        skill_id: str,
    ) -> list[SkillNode]:

        stmt = (
            select(SkillNode)
            .join(
                SkillEdge,
                SkillEdge.prerequisite_id == SkillNode.id,
            )
            .where(
                SkillEdge.dependent_id == skill_id
            )
        )

        return list(self.db.scalars(stmt).all())

    def get_dependents(
        self,
        skill_id: str,
    ) -> list[SkillNode]:

        stmt = (
            select(SkillNode)
            .join(
                SkillEdge,
                SkillEdge.dependent_id == SkillNode.id,
            )
            .where(
                SkillEdge.prerequisite_id == skill_id
            )
        )

        return list(self.db.scalars(stmt).all())

    def get_all_prerequisites(
        self,
        skill_id: str,
    ) -> set[str]:

        visited: set[str] = set()
        stack = [skill_id]

        while stack:
            current = stack.pop()

            for prerequisite in self.get_prerequisites(current):
                if prerequisite.id not in visited:
                    visited.add(prerequisite.id)
                    stack.append(prerequisite.id)

        return visited

    def get_all_dependents(
        self,
        skill_id: str,
    ) -> set[str]:

        visited: set[str] = set()
        stack = [skill_id]

        while stack:
            current = stack.pop()

            for dependent in self.get_dependents(current):
                if dependent.id not in visited:
                    visited.add(dependent.id)
                    stack.append(dependent.id)

        return visited