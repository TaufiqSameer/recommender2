from sqlalchemy import text

from app.db.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.scalar()

        print("Database connection successful!")
        print(version)

except Exception as e:
    print("Database connection failed!")
    print(e)