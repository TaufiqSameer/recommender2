from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SkillEdge, SkillNode


class SkillGraph:
    def __init__(self, db: Session):
        self.db = db

    def get_skill(self, skill_id: str) -> SkillNode | None:
        return self.db.get(SkillNode, skill_id)

    def get_prerequisites(self, skill_id: str) -> list[SkillNode]:
        stmt = (
            select(SkillNode)
            .join(
                SkillEdge,
                SkillEdge.prerequisite_id == SkillNode.id,
            )
            .where(SkillEdge.dependent_id == skill_id)
        )

        return list(self.db.scalars(stmt).all())

    def get_dependents(self, skill_id: str) -> list[SkillNode]:
        stmt = (
            select(SkillNode)
            .join(
                SkillEdge,
                SkillEdge.dependent_id == SkillNode.id,
            )
            .where(SkillEdge.prerequisite_id == skill_id)
        )

        return list(self.db.scalars(stmt).all())

    def get_all_skills(self) -> list[SkillNode]:
        stmt = select(SkillNode)
        return list(self.db.scalars(stmt).all())