from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.learning import (
    ActivitySubmission,
)

from sqlalchemy import select

from app.db.models import (
    LearnerSkillState,
    LearningActivity,
)

from app.db.database import get_db

from app.services.learning.adaptive_loop import (
    AdaptiveLearningService,
)
from sqlalchemy import select

from app.db.models import LearnerSkillState


router = APIRouter(
    prefix="/api/learners",
    tags=["learning"],
)


# =========================================================
# GET NEXT ACTIVITY
# =========================================================


@router.get(
    "/{learner_id}/next-activity"
)
def get_next_activity(
    learner_id: str,
    db: Session = Depends(get_db),
):

    service = (
        AdaptiveLearningService(db)
    )

    try:

        result = (
            service.generate_next_activity(
                learner_id
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "No learning activity "
                "is currently available."
            ),
        )

    return {
        "activity_id": result.activity_id,

        "skill": {
            "id": (
                result.recommendation.skill.id
            ),

            "label": (
                result.recommendation.skill.label
            ),
        },

        "recommendation": {
            "score": (
                result.recommendation.score
            ),

            "reason": (
                result.recommendation.reason
            ),
        },

        "activity": {
            "title": (
                result.activity.title
            ),

            "type": (
                result.activity.activity_type
            ),

            "objective": (
                result.activity.objective
            ),

            "difficulty": (
                result.activity.difficulty
            ),

            "instructions": (
                result.activity.instructions
            ),

            "hints": (
                result.activity.hints
            ),
        },
    }


# =========================================================
# SUBMIT ACTIVITY
# =========================================================


@router.post(
    "/{learner_id}/activities/{activity_id}/submit"
)
def submit_activity(
    learner_id: str,
    activity_id: str,
    submission: ActivitySubmission,
    db: Session = Depends(get_db),
):

    service = (
        AdaptiveLearningService(db)
    )

    try:

        result = (
            service.evaluate_response(
                learner_id=learner_id,

                activity_id=activity_id,

                learner_answer=(
                    submission.answer
                ),
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return {
        "activity_id": activity_id,

        "evaluation": {
            "score": (
                result.evaluation.score
            ),

            "correct": (
                result.evaluation.correct
            ),

            "feedback": (
                result.evaluation.feedback
            ),

            "strengths": (
                result.evaluation.strengths
            ),

            "weaknesses": (
                result.evaluation.weaknesses
            ),

            "next_step": (
                result.evaluation.next_step
            ),
        },

        "learner_state": {
            "skill_id": (
                result.feedback.state.skill_id
            ),

            "mastery": (
                result.feedback.state.mastery
            ),

            "theta": (
                result.feedback.state.theta
            ),

            "confidence": (
                result.feedback.state.confidence
            ),

            "attempts": (
                result.feedback.state.attempts
            ),

            "status": (
                result.feedback.state.status
            ),
        },
    }
    
@router.get(
    "/{learner_id}/state"
)
def get_learner_state(
    learner_id: str,
    db: Session = Depends(get_db),
):
    states = list(
        db.scalars(
            select(LearnerSkillState)
            .where(
                LearnerSkillState.learner_id
                == learner_id
            )
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
                "last_assessed_at": (
                    state.last_assessed_at
                ),
            }
            for state in states
        ],
    }
    
@router.get(
    "/{learner_id}/activities"
)
def get_activity_history(
    learner_id: str,
    db: Session = Depends(get_db),
):
    activities = list(
        db.scalars(
            select(LearningActivity)
            .where(
                LearningActivity.learner_id
                == learner_id
            )
            .order_by(
                LearningActivity.created_at.desc()
            )
        ).all()
    )

    return {
        "learner_id": learner_id,
        "activities": [
            {
                "activity_id": activity.id,

                "skill_id": (
                    activity.skill_id
                ),

                "title": (
                    activity.title
                ),

                "type": (
                    activity.activity_type
                ),

                "objective": (
                    activity.objective
                ),

                "difficulty": (
                    activity.difficulty
                ),

                "instructions": (
                    activity.instructions
                ),

                "hints": (
                    activity.hints
                ),

                "recommendation_score": (
                    activity.recommendation_score
                ),

                "generation_source": (
                    activity.generation_source
                ),

                "created_at": (
                    activity.created_at
                ),
            }
            for activity in activities
        ],
    }