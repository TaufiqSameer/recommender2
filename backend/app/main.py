from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import Base, engine
from app.db import models  # noqa: F401 — ensures all tables are registered

from app.api.routes.auth import router as auth_router
from app.api.routes.learning import router as learning_router
from app.api.routes.onboarding import router as onboarding_router
from app.api.routes.chat_sessions import router as chat_router
from app.api.routes.progress import router as progress_router
from app.api.routes.graph import router as graph_router


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(learning_router)
app.include_router(onboarding_router)
app.include_router(chat_router)
app.include_router(progress_router)
app.include_router(graph_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}