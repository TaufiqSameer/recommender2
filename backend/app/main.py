from fastapi import FastAPI

from app.config import settings

from app.db.database import Base, engine

from app.db import models

from app.api.routes.learning import (
    router as learning_router,
)


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


app.include_router(
    learning_router
)


@app.get("/health")
def health() -> dict[str, str]:

    return {
        "status": "ok"
    }