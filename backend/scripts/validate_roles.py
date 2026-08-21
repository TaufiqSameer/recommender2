from app.db.database import SessionLocal
from app.db.models import SkillNode
from app.services.goals.goal_mapper import GoalMapper


def main() -> None:

    mapper = GoalMapper()

    with SessionLocal() as db:

        skills = {
            skill.id
            for skill in db.query(SkillNode).all()
        }

        print("Validating role definitions...\n")

        for role in mapper.list_roles():

            print(
                f"Checking role: {role['label']}"
            )

            for skill_id in role["required_skills"]:

                if skill_id not in skills:
                    raise ValueError(
                        f"Role '{role['id']}' references "
                        f"unknown skill '{skill_id}'."
                    )

        print("\n✓ All role skill references are valid.")


if __name__ == "__main__":
    main()