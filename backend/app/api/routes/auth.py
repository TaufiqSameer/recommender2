import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models.learner import LearnerProfile
from app.db.models.user import User


router = APIRouter(prefix="/api/auth", tags=["auth"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    learner_id: str
    username: str
    display_name: str | None


# ─── Signup ──────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    body: SignupRequest,
    db: Session = Depends(get_db),
):
    # Check uniqueness
    existing_email = db.scalars(
        select(User).where(User.email == body.email)
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    existing_username = db.scalars(
        select(User).where(User.username == body.username)
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken.",
        )

    # Create user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()

    # Create linked learner profile
    learner_id = f"learner-{user_id[:8]}"
    display_name = body.display_name or body.username
    learner = LearnerProfile(
        learner_id=learner_id,
        user_id=user.id,
        display_name=display_name,
        onboarding_state="NEW",
        learning_preferences=[],
        preferences={},
    )
    db.add(learner)
    db.commit()

    token = create_access_token(subject=user_id)

    return TokenResponse(
        access_token=token,
        learner_id=learner_id,
        username=user.username,
        display_name=display_name,
    )


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalars(
        select(User).where(User.email == body.email)
    ).first()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    learner = db.scalars(
        select(LearnerProfile).where(LearnerProfile.user_id == user.id)
    ).first()

    if learner is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Learner profile not found.",
        )

    token = create_access_token(subject=user.id)

    return TokenResponse(
        access_token=token,
        learner_id=learner.learner_id,
        username=user.username,
        display_name=learner.display_name,
    )


# ─── Me ──────────────────────────────────────────────────────────────────────

class MeResponse(BaseModel):
    user_id: str
    email: str
    username: str
    learner_id: str
    display_name: str | None = None
    onboarding_state: str
    goal: str | None = None
    target_role: str | None = None
    domain: str | None = None
    weekly_hours: float | None = None
    learning_preferences: list | None = None
    preferences: dict | None = None


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
    goal: str | None = None
    target_role: str | None = None
    domain: str | None = None
    weekly_hours: float | None = None
    learning_preferences: list | None = None
    preferences: dict | None = None


@router.get("/me", response_model=MeResponse)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = db.scalars(
        select(LearnerProfile).where(
            LearnerProfile.user_id == current_user.id
        )
    ).first()

    if learner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found.",
        )

    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        learner_id=learner.learner_id,
        display_name=learner.display_name,
        onboarding_state=learner.onboarding_state,
        goal=learner.goal,
        target_role=learner.target_role,
        domain=learner.domain,
        weekly_hours=learner.weekly_hours,
        learning_preferences=learner.learning_preferences,
        preferences=learner.preferences,
    )


@router.patch("/me", response_model=MeResponse)
def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = db.scalars(
        select(LearnerProfile).where(
            LearnerProfile.user_id == current_user.id
        )
    ).first()

    if learner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found.",
        )

    if body.display_name is not None:
        learner.display_name = body.display_name
    if body.goal is not None:
        learner.goal = body.goal
    if body.target_role is not None:
        learner.target_role = body.target_role
    if body.domain is not None:
        learner.domain = body.domain
    if body.weekly_hours is not None:
        learner.weekly_hours = body.weekly_hours
    if body.learning_preferences is not None:
        learner.learning_preferences = body.learning_preferences
    if body.preferences is not None:
        prefs = dict(learner.preferences or {})
        prefs.update(body.preferences)
        learner.preferences = prefs

    db.commit()

    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        learner_id=learner.learner_id,
        display_name=learner.display_name,
        onboarding_state=learner.onboarding_state,
        goal=learner.goal,
        target_role=learner.target_role,
        domain=learner.domain,
        weekly_hours=learner.weekly_hours,
        learning_preferences=learner.learning_preferences,
        preferences=learner.preferences,
    )
