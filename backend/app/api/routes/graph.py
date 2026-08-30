from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.learner import LearnerProfile, LearnerSkillState
from app.db.models.skill import SkillEdge, SkillNode
from app.db.models.user import User


router = APIRouter(prefix="/api/graph", tags=["graph"])


def _get_learner(user: User, db: Session) -> LearnerProfile:
    from fastapi import HTTPException
    learner = db.scalars(
        select(LearnerProfile).where(LearnerProfile.user_id == user.id)
    ).first()
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


@router.get("")
@router.get("/")
@router.get("/skills")
def get_skill_graph(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(current_user, db)
    lid = learner.learner_id
    domain = learner.domain

    # Get skill nodes (filter to domain if matches, or fallback to all skills)
    skills = []
    if domain:
        skills = list(db.scalars(select(SkillNode).where(SkillNode.domain == domain)))
    if not skills:
        skills = list(db.scalars(select(SkillNode)))

    # Get learner states indexed by skill_id
    states = {
        s.skill_id: s
        for s in db.scalars(
            select(LearnerSkillState).where(LearnerSkillState.learner_id == lid)
        )
    }

    skill_ids = {s.id for s in skills}

    # Get edges
    edges = list(db.scalars(
        select(SkillEdge).where(
            SkillEdge.prerequisite_id.in_(skill_ids),
            SkillEdge.dependent_id.in_(skill_ids),
        )
    ))

    nodes = []
    for skill in skills:
        state = states.get(skill.id)
        mastery = state.mastery if state else 0.0
        status = state.status if state else "locked"

        nodes.append({
            "id": skill.id,
            "label": skill.label,
            "domain": skill.domain,
            "difficulty": skill.difficulty,
            "mastery": round(mastery, 3),
            "status": status,
            "attempts": state.attempts if state else 0,
        })

    edge_list = [
        {
            "source": e.prerequisite_id,
            "target": e.dependent_id,
        }
        for e in edges
    ]

    return {
        "nodes": nodes,
        "edges": edge_list,
        "domain": domain,
    }
