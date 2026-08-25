from app.db.database import Base, engine

# Import all models so SQLAlchemy registers them
# with Base.metadata.
import app.db.models  # noqa: F401


def main():

    print(
        "Creating missing database tables..."
    )

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Database tables are ready."
    )


if __name__ == "__main__":
    main()