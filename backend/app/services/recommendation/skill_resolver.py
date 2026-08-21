from sqlalchemy.orm import Session

from app.db.models import SkillNode


class SkillResolver:

    def __init__(self, db: Session):
        self.db = db

    def resolve(
        self,
        skill_names: list[str],
    ) -> dict[str, SkillNode | None]:

        skills = (
            self.db.query(SkillNode)
            .all()
        )

        by_id = {
            skill.id.lower(): skill
            for skill in skills
        }

        by_label = {
            skill.label.lower(): skill
            for skill in skills
        }

        resolved = {}

        for name in skill_names:

            normalized = name.strip().lower()

            skill = (
                by_id.get(normalized)
                or by_label.get(normalized)
            )

            resolved[name] = skill

        return resolved