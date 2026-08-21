from app.db.database import Base, engine

from app.db.models import (
    LearnerProfile,
    LearnerSkillState,
    SkillEdge,
    SkillNode,
)


def reset_database() -> None:
    print("Dropping development tables...")

    Base.metadata.drop_all(bind=engine)

    print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    print("Database reset successfully.")


if __name__ == "__main__":
    reset_database()