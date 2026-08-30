from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.learner import LearnerEvidence, LearnerProfile, LearnerSkillState
from app.db.models.learning_activity import LearningActivity
from app.db.models.skill import SkillNode
from app.db.models.user import User


router = APIRouter(prefix="/api/progress", tags=["progress"])


def _get_learner(user: User, db: Session) -> LearnerProfile:
    from fastapi import HTTPException
    learner = db.scalars(
        select(LearnerProfile).where(LearnerProfile.user_id == user.id)
    ).first()
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


@router.get("")
def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    lid = learner.learner_id

    # Skill states
    states = list(db.scalars(
        select(LearnerSkillState).where(LearnerSkillState.learner_id == lid)
    ))

    overall_mastery = (
        sum(s.mastery for s in states) / len(states) if states else 0.0
    )

    skills_mastered = sum(1 for s in states if s.mastery >= 0.8)
    skills_learning = sum(1 for s in states if 0.1 <= s.mastery < 0.8)

    # Activities completed (via evidence)
    completed_ids = {
        ev.source_id
        for ev in db.scalars(
            select(LearnerEvidence).where(
                LearnerEvidence.learner_id == lid,
                LearnerEvidence.evidence_type == "ai_evaluation",
            )
        )
        if ev.source_id
    }
    activities_completed = len(completed_ids)

    # Mastery over time — from evidence timestamps
    evidence_timeline = [
        {
            "date": ev.created_at.date().isoformat(),
            "score": ev.score,
            "skill_id": ev.skill_id,
        }
        for ev in db.scalars(
            select(LearnerEvidence)
            .where(LearnerEvidence.learner_id == lid)
            .order_by(LearnerEvidence.created_at.asc())
            .limit(100)
        )
    ]

    # Skill mastery breakdown
    skill_mastery = []
    for state in sorted(states, key=lambda s: s.mastery, reverse=True):
        skill = db.get(SkillNode, state.skill_id)
        skill_mastery.append({
            "skill_id": state.skill_id,
            "label": skill.label if skill else state.skill_id,
            "mastery": round(state.mastery, 3),
            "status": state.status,
            "attempts": state.attempts,
        })

    # Streak (days with at least one evidence item)
    import datetime as dt
    today = dt.date.today()
    streak = 0
    for i in range(60):
        day = today - dt.timedelta(days=i)
        has_activity = any(
            ev["date"] == day.isoformat()
            for ev in evidence_timeline
        )
        if has_activity:
            streak += 1
        elif i > 0:
            break

    return {
        "overall_mastery": round(overall_mastery, 3),
        "skills_mastered": skills_mastered,
        "skills_learning": skills_learning,
        "activities_completed": activities_completed,
        "streak_days": streak,
        "skill_mastery": skill_mastery,
        "evidence_timeline": evidence_timeline,
    }
