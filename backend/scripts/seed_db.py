import json
from pathlib import Path

from sqlalchemy import select

from app.db.database import Base, SessionLocal, engine
from app.db.models import SkillEdge, SkillNode
from app.services.skill_graph.validation import validate_graph


SEED_FILE = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "seed"
    / "backend_skills.json"
)


def load_seed_data() -> dict:
    with SEED_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_models(data: dict) -> tuple[list[SkillNode], list[SkillEdge]]:
    skills_data = data["skills"]

    skills = []
    edges = []

    skill_ids = {skill["id"] for skill in skills_data}

    # Validate prerequisite references before creating database objects.
    for skill in skills_data:
        for prerequisite_id in skill.get("prerequisites", []):
            if prerequisite_id not in skill_ids:
                raise ValueError(
                    f"Skill '{skill['id']}' references unknown "
                    f"prerequisite '{prerequisite_id}'."
                )

            if prerequisite_id == skill["id"]:
                raise ValueError(
                    f"Skill '{skill['id']}' cannot depend on itself."
                )

    # Create SkillNode objects.
    for skill in skills_data:
        skills.append(
            SkillNode(
                id=skill["id"],
                domain=data["domain"],
                label=skill["label"],
                description=skill["description"],
                difficulty=skill["difficulty"],
                learning_objectives=skill["learning_objectives"],
            )
        )

    # Create SkillEdge objects.
    seen_edges: set[tuple[str, str]] = set()

    for skill in skills_data:
        for prerequisite_id in skill.get("prerequisites", []):
            edge = (prerequisite_id, skill["id"])

            if edge in seen_edges:
                raise ValueError(
                    f"Duplicate prerequisite edge: "
                    f"{prerequisite_id} -> {skill['id']}"
                )

            seen_edges.add(edge)

            edges.append(
                SkillEdge(
                    prerequisite_id=prerequisite_id,
                    dependent_id=skill["id"],
                )
            )

    return skills, edges


def seed_database() -> None:
    print("Loading skill graph...")

    data = load_seed_data()

    print(f"Domain: {data['domain']}")
    print(f"Version: {data['version']}")

    skills, edges = build_models(data)

    print(f"Found {len(skills)} skills.")
    print(f"Found {len(edges)} prerequisite edges.")

    # Validate the complete graph before touching the database.
    print("\nValidating graph...")

    validate_graph(skills, edges)

    print("✓ All prerequisite references are valid.")
    print("✓ No self-dependencies found.")
    print("✓ No duplicate edges found.")
    print("✓ Graph is a valid DAG.")

    # Make sure tables exist.
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        print("\nSeeding database...")

        # Remove existing graph data so the seed is deterministic.
        db.query(SkillEdge).delete()
        db.query(SkillNode).delete()

        db.add_all(skills)
        db.flush()

        db.add_all(edges)

        db.commit()

        print(f"✓ Inserted {len(skills)} skill nodes.")
        print(f"✓ Inserted {len(edges)} skill edges.")

    print("\nSeed completed successfully.")


if __name__ == "__main__":
    seed_database()