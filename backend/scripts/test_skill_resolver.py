from app.db.database import SessionLocal
from app.services.recommendation.skill_resolver import (
    SkillResolver,
)


def main() -> None:

    with SessionLocal() as db:

        resolver = SkillResolver(db)

        names = [
            "SQL",
            "FastAPI",
            "REST API Design",
            "Python",
            "APIs",
        ]

        results = resolver.resolve(names)

        print("\nSkill resolution:\n")

        for name, skill in results.items():

            if skill is None:
                print(
                    f"{name} -> NOT FOUND"
                )
            else:
                print(
                    f"{name} -> "
                    f"{skill.id} "
                    f"({skill.label})"
                )


if __name__ == "__main__":
    main()