from app.db.database import Base, engine

# Import models so SQLAlchemy registers them with Base.
from app.db.models import (
    LearnerProfile,
    LearnerSkillState,
    SkillEdge,
    SkillNode,
)


def init_db() -> None:
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()