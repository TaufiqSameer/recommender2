from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.learner import LearnerProfile
from app.db.models.user import User
from app.services.onboarding.onboarding_service import OnboardingService


router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def _get_learner(user: User, db: Session) -> LearnerProfile:
    learner = db.scalars(
        select(LearnerProfile).where(LearnerProfile.user_id == user.id)
    ).first()
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class OnboardingChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class AssessmentAnswerRequest(BaseModel):
    attempt_id: str
    answer: str


class OnboardingChatResponse(BaseModel):
    message: str
    state: str
    progress: int
    assessment_question: dict | None = None
    assessment_complete: bool = False


class OnboardingStatusResponse(BaseModel):
    state: str
    learner_id: str
    goal: str | None = None
    domain: str | None = None
    display_name: str | None = None
    progress: int = 0
    assessment_question: dict | None = None
    assessment_complete: bool = False
    message: str | None = None


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/status", response_model=OnboardingStatusResponse)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    service = OnboardingService(db)
    progress = service._progress(learner.onboarding_state)
    assessment_q = None
    msg = None

    if learner.onboarding_state == "ASSESSMENT":
        res = service._start_assessment(learner)
        assessment_q = res.assessment_question
        msg = res.message
        progress = res.progress

    return OnboardingStatusResponse(
        state=learner.onboarding_state,
        learner_id=learner.learner_id,
        goal=learner.goal,
        domain=learner.domain,
        display_name=learner.display_name,
        progress=progress,
        assessment_question=assessment_q,
        assessment_complete=learner.onboarding_state in ("PROFILE_READY", "LEARNING"),
        message=msg,
    )


@router.post("/chat", response_model=OnboardingChatResponse)
def onboarding_chat(
    body: OnboardingChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    service = OnboardingService(db)

    result = service.chat(
        learner_id=learner.learner_id,
        message=body.message,
        history=[{"role": m.role, "content": m.content} for m in body.history],
    )

    return OnboardingChatResponse(
        message=result.message,
        state=result.state,
        progress=result.progress,
        assessment_question=result.assessment_question,
        assessment_complete=result.assessment_complete,
    )


@router.post("/assessment/answer", response_model=OnboardingChatResponse)
def submit_assessment_answer(
    body: AssessmentAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    service = OnboardingService(db)

    result = service.submit_assessment_answer(
        learner_id=learner.learner_id,
        attempt_id=body.attempt_id,
        answer=body.answer,
    )

    return OnboardingChatResponse(
        message=result.message,
        state=result.state,
        progress=result.progress,
        assessment_question=result.assessment_question,
        assessment_complete=result.assessment_complete,
    )


@router.post("/complete")
def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    service = OnboardingService(db)
    service.complete_onboarding(learner.learner_id)
    return {"status": "ok", "state": "LEARNING"}
