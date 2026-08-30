import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.learner import LearnerProfile
from app.db.models.user import User
from app.services.learning.chat import LearningChatService


router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_learner(user: User, db: Session) -> LearnerProfile:
    learner = db.scalars(
        select(LearnerProfile).where(LearnerProfile.user_id == user.id)
    ).first()
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: str = "New conversation"


class SendMessageRequest(BaseModel):
    content: str
    activity_id: str | None = None


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/sessions", status_code=201)
def create_session(
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    session = ChatSession(
        id=str(uuid.uuid4()),
        learner_id=learner.learner_id,
        title=body.title,
    )
    db.add(session)
    db.commit()
    return {"id": session.id, "title": session.title, "created_at": session.created_at}


@router.get("/sessions")
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    sessions = list(db.scalars(
        select(ChatSession)
        .where(ChatSession.learner_id == learner.learner_id)
        .order_by(ChatSession.updated_at.desc())
    ))
    return {
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in sessions
        ]
    }


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    session = db.get(ChatSession, session_id)

    if session is None or session.learner_id != learner.learner_id:
        raise HTTPException(status_code=404, detail="Session not found.")

    messages = list(db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    ))

    return {
        "id": session.id,
        "title": session.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


@router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: str,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    session = db.get(ChatSession, session_id)

    if session is None or session.learner_id != learner.learner_id:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Save user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)

    # Build conversation history for the tutor
    past_messages = list(db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    ))

    history = [
        {"role": m.role, "content": m.content}
        for m in past_messages
    ]

    # Call the tutor
    service = LearningChatService(db)
    try:
        result = service.respond(
            learner_id=learner.learner_id,
            message=body.content,
            activity_id=body.activity_id,
            conversation_history=history,
        )
        assistant_content = result.message
    except Exception:
        assistant_content = (
            "LearnAI is temporarily unavailable. "
            "Your progress is safe. Please try again."
        )

    # Save assistant message
    assistant_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_msg)

    # Update session title from first user message
    if len(past_messages) == 0 and session.title == "New conversation":
        session.title = body.content[:60]

    db.commit()

    return {
        "user_message": {
            "id": user_msg.id,
            "role": "user",
            "content": user_msg.content,
        },
        "assistant_message": {
            "id": assistant_msg.id,
            "role": "assistant",
            "content": assistant_content,
        },
    }
