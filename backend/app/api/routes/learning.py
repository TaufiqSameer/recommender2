from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.learning import (
    ActivitySubmission,
)

from sqlalchemy import select
from app.api.schemas.chat import (
    LearningChatRequest,
)

from app.services.learning.chat import (
    LearningChatService,
)

from app.db.models import (
    LearnerEvidence,
    LearnerSkillState,
    LearningActivity,
)

from app.db.models.learner import LearnerProfile
from app.db.models.skill import SkillNode
from app.db.database import get_db
from app.auth.dependencies import get_current_user
from app.db.models.user import User

from app.services.learning.adaptive_loop import (
    AdaptiveLearningService,
)


router = APIRouter(
    prefix="/api/learners",
    tags=["learning"],
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _resolve_learner(
    current_user: User,
    db: Session,
) -> str:
    """Derive the learner_id from the authenticated user."""
    learner = db.scalars(
        select(LearnerProfile).where(
            LearnerProfile.user_id == current_user.id
        )
    ).first()
    if learner is None:
        raise HTTPException(
            status_code=404,
            detail="Learner profile not found.",
        )
    return learner.learner_id


# =========================================================
# GET NEXT ACTIVITY
# =========================================================


@router.get("/me/next-activity")
def get_next_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner_id = _resolve_learner(current_user, db)
    service = AdaptiveLearningService(db)

    try:
        result = service.generate_next_activity(learner_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No learning activity is currently available.",
        )

    return {
        "activity_id": result.activity_id,
        "skill": {
            "id": result.recommendation.skill.id,
            "label": result.recommendation.skill.label,
        },
        "recommendation": {
            "score": result.recommendation.score,
            "reason": result.recommendation.reason,
        },
        "activity": {
            "title": result.activity.title,
            "type": result.activity.activity_type,
            "objective": result.activity.objective,
            "difficulty": result.activity.difficulty,
            "instructions": result.activity.instructions,
            "hints": result.activity.hints,
        },
    }


# =========================================================
# SUBMIT ACTIVITY
# =========================================================


@router.post("/me/activities/{activity_id}/submit")
def submit_activity(
    activity_id: str,
    submission: ActivitySubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner_id = _resolve_learner(current_user, db)
    service = AdaptiveLearningService(db)

    try:
        result = service.evaluate_response(
            learner_id=learner_id,
            activity_id=activity_id,
            learner_answer=submission.answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "activity_id": activity_id,
        "evaluation": {
            "score": result.evaluation.score,
            "correct": result.evaluation.correct,
            "feedback": result.evaluation.feedback,
            "strengths": result.evaluation.strengths,
            "weaknesses": result.evaluation.weaknesses,
            "next_step": result.evaluation.next_step,
        },
        "learner_state": {
            "skill_id": result.feedback.state.skill_id,
            "mastery": result.feedback.state.mastery,
            "theta": result.feedback.state.theta,
            "confidence": result.feedback.state.confidence,
            "attempts": result.feedback.state.attempts,
            "status": result.feedback.state.status,
        },
    }


# =========================================================
# LEARNER STATE
# =========================================================


@router.get("/me/state")
def get_learner_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner_id = _resolve_learner(current_user, db)
    states = list(
        db.scalars(
            select(LearnerSkillState)
            .where(LearnerSkillState.learner_id == learner_id)
        ).all()
    )

    return {
        "learner_id": learner_id,
        "skills": [
            {
                "skill_id": state.skill_id,
                "mastery": state.mastery,
                "theta": state.theta,
                "confidence": state.confidence,
                "attempts": state.attempts,
                "status": state.status,
                "last_assessed_at": state.last_assessed_at,
            }
            for state in states
        ],
    }


# =========================================================
# ACTIVITY HISTORY
# =========================================================


@router.get("/me/activities")
def get_learner_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner_id = _resolve_learner(current_user, db)
    activities = list(
        db.scalars(
            select(LearningActivity)
            .where(LearningActivity.learner_id == learner_id)
            .order_by(LearningActivity.created_at.desc())
        )
    )

    evidence = list(
        db.scalars(
            select(LearnerEvidence)
            .where(
                LearnerEvidence.learner_id == learner_id,
                LearnerEvidence.evidence_type == "ai_evaluation",
            )
        )
    )

    # Evidence indexed by source_id for fast lookup
    evidence_by_activity = {}
    for ev in evidence:
        if ev.source_id:
            evidence_by_activity.setdefault(ev.source_id, []).append(ev)

    completed_activity_ids = set(evidence_by_activity.keys())

    # Enrich with skill labels
    skill_ids = {a.skill_id for a in activities}
    skills = {
        s.id: s
        for s in db.scalars(
            select(SkillNode).where(SkillNode.id.in_(skill_ids))
        )
    }

    return {
        "learner_id": learner_id,
        "activities_completed": len(completed_activity_ids),
        "activities": [
            {
                "activity_id": activity.id,
                "skill_id": activity.skill_id,
                "skill_label": skills.get(activity.skill_id, SkillNode(label=activity.skill_id)).label if activity.skill_id in skills else activity.skill_id,
                "title": activity.title,
                "type": activity.activity_type,
                "objective": activity.objective,
                "difficulty": activity.difficulty,
                "instructions": activity.instructions,
                "hints": activity.hints,
                "recommendation_score": activity.recommendation_score,
                "generation_source": activity.generation_source,
                "created_at": activity.created_at,
                "completed": activity.id in completed_activity_ids,
                "score": (
                    evidence_by_activity[activity.id][0].score
                    if activity.id in evidence_by_activity
                    else None
                ),
            }
            for activity in activities
        ],
    }


# =========================================================
# LEARNING CHAT (direct / stateless)
# =========================================================


@router.post("/me/chat")
def learning_chat(
    request: LearningChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner_id = _resolve_learner(current_user, db)
    service = LearningChatService(db)

    try:
        result = service.respond(
            learner_id=learner_id,
            message=request.message,
            activity_id=request.activity_id,
            conversation_history=[
                {"role": item.role, "content": item.content}
                for item in request.conversation_history
            ],
        )
    except Exception:
        return {
            "message": (
                "EurekaAI is temporarily unavailable. "
                "Your progress is safe. Please try again."
            ),
            "context": {
                "skill_id": None,
                "mastery": None,
                "confidence": None,
            },
        }

    return {
        "message": result.message,
        "context": {
            "skill_id": result.skill_id,
            "mastery": result.mastery,
            "confidence": result.confidence,
        },
    }


# =========================================================
# LEGACY ROUTES (backward-compatible, still accept learner_id in path)
# These are kept so the old Learn page still works during migration.
# =========================================================


@router.get("/{learner_id}/next-activity")
def get_next_activity_legacy(
    learner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ownership
    owned_id = _resolve_learner(current_user, db)
    if owned_id != learner_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    service = AdaptiveLearningService(db)
    try:
        result = service.generate_next_activity(learner_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="No learning activity is currently available.")

    return {
        "activity_id": result.activity_id,
        "skill": {
            "id": result.recommendation.skill.id,
            "label": result.recommendation.skill.label,
        },
        "recommendation": {
            "score": result.recommendation.score,
            "reason": result.recommendation.reason,
        },
        "activity": {
            "title": result.activity.title,
            "type": result.activity.activity_type,
            "objective": result.activity.objective,
            "difficulty": result.activity.difficulty,
            "instructions": result.activity.instructions,
            "hints": result.activity.hints,
        },
    }


@router.post("/{learner_id}/activities/{activity_id}/submit")
def submit_activity_legacy(
    learner_id: str,
    activity_id: str,
    submission: ActivitySubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned_id = _resolve_learner(current_user, db)
    if owned_id != learner_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    service = AdaptiveLearningService(db)
    try:
        result = service.evaluate_response(
            learner_id=learner_id,
            activity_id=activity_id,
            learner_answer=submission.answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "activity_id": activity_id,
        "evaluation": {
            "score": result.evaluation.score,
            "correct": result.evaluation.correct,
            "feedback": result.evaluation.feedback,
            "strengths": result.evaluation.strengths,
            "weaknesses": result.evaluation.weaknesses,
            "next_step": result.evaluation.next_step,
        },
        "learner_state": {
            "skill_id": result.feedback.state.skill_id,
            "mastery": result.feedback.state.mastery,
            "theta": result.feedback.state.theta,
            "confidence": result.feedback.state.confidence,
            "attempts": result.feedback.state.attempts,
            "status": result.feedback.state.status,
        },
    }


@router.get("/{learner_id}/state")
def get_learner_state_legacy(
    learner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned_id = _resolve_learner(current_user, db)
    if owned_id != learner_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    states = list(
        db.scalars(
            select(LearnerSkillState)
            .where(LearnerSkillState.learner_id == learner_id)
        ).all()
    )
    return {
        "learner_id": learner_id,
        "skills": [
            {
                "skill_id": state.skill_id,
                "mastery": state.mastery,
                "theta": state.theta,
                "confidence": state.confidence,
                "attempts": state.attempts,
                "status": state.status,
                "last_assessed_at": state.last_assessed_at,
            }
            for state in states
        ],
    }


@router.get("/{learner_id}/activities")
def get_learner_activities_legacy(
    learner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned_id = _resolve_learner(current_user, db)
    if owned_id != learner_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    activities = list(
        db.scalars(
            select(LearningActivity)
            .where(LearningActivity.learner_id == learner_id)
            .order_by(LearningActivity.created_at.desc())
        )
    )

    evidence = list(
        db.scalars(
            select(LearnerEvidence)
            .where(
                LearnerEvidence.learner_id == learner_id,
                LearnerEvidence.evidence_type == "ai_evaluation",
            )
        )
    )

    completed_activity_ids = {
        item.source_id for item in evidence if item.source_id
    }

    return {
        "learner_id": learner_id,
        "activities_completed": len(completed_activity_ids),
        "activities": [
            {
                "activity_id": activity.id,
                "skill_id": activity.skill_id,
                "title": activity.title,
                "type": activity.activity_type,
                "objective": activity.objective,
                "difficulty": activity.difficulty,
                "instructions": activity.instructions,
                "hints": activity.hints,
                "recommendation_score": activity.recommendation_score,
                "generation_source": activity.generation_source,
                "created_at": activity.created_at,
            }
            for activity in activities
        ],
    }


@router.post("/{learner_id}/chat")
def learning_chat_legacy(
    learner_id: str,
    request: LearningChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned_id = _resolve_learner(current_user, db)
    if owned_id != learner_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    service = LearningChatService(db)
    try:
        result = service.respond(
            learner_id=learner_id,
            message=request.message,
            activity_id=request.activity_id,
            conversation_history=[
                {"role": item.role, "content": item.content}
                for item in request.conversation_history
            ],
        )
    except Exception:
        return {
            "message": (
                "EurekaAI is temporarily unavailable. "
                "Your progress is safe. Please try again."
            ),
            "context": {"skill_id": None, "mastery": None, "confidence": None},
        }

    return {
        "message": result.message,
        "context": {
            "skill_id": result.skill_id,
            "mastery": result.mastery,
            "confidence": result.confidence,
        },
    }