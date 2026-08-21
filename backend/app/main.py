from fastapi import FastAPI

from app.config import settings
from app.db.database import Base, engine

from app.db import models 


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}