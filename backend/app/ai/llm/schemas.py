from pydantic import BaseModel, Field


class LearnerIntent(BaseModel):
    goal: str = Field(
        description=(
            "The learner's primary career or learning goal."
        )
    )

    known_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Skills the learner claims to already know."
        ),
    )

    weekly_hours: float | None = Field(
        default=None,
        description=(
            "Approximate number of hours the learner "
            "can study per week."
        ),
    )

    learning_style: str | None = Field(
        default=None,
        description=(
            "Preferred learning approach, such as "
            "project_based, theory_first, video, "
            "documentation, or mixed."
        ),
    )

    focus_areas: list[str] = Field(
        default_factory=list,
        description=(
            "Specific technologies, topics, or areas "
            "the learner wants to focus on."
        ),
    )


class LearningActivity(BaseModel):
    """
    A concrete learning activity generated for a learner
    based on a skill selected by the adaptive engine.
    """

    title: str = Field(
        description=(
            "Short title for the learning activity."
        )
    )

    activity_type: str = Field(
        description=(
            "Type of activity, such as "
            "coding_exercise, quiz, explanation, "
            "debugging, or project."
        )
    )

    objective: str = Field(
        description=(
            "The specific learning objective "
            "the learner should achieve."
        )
    )

    instructions: str = Field(
        description=(
            "Clear instructions describing exactly "
            "what the learner should do."
        )
    )

    difficulty: str = Field(
        description=(
            "Difficulty level appropriate for the "
            "learner's current state."
        )
    )

    hints: list[str] = Field(
        default_factory=list,
        description=(
            "Optional hints that can help the learner "
            "without directly giving away the solution."
        ),
    )
    
class LearningEvaluation(BaseModel):
    """
    Structured evaluation of a learner's response
    to a learning activity.
    """

    score: float = Field(
        description=(
            "A score between 0.0 and 1.0 representing "
            "how well the learner completed the activity."
        ),
        ge=0.0,
        le=1.0,
    )

    correct: bool = Field(
        description=(
            "Whether the learner's answer is "
            "substantially correct."
        )
    )

    feedback: str = Field(
        description=(
            "Clear and constructive feedback explaining "
            "the learner's performance."
        )
    )

    strengths: list[str] = Field(
        default_factory=list,
        description=(
            "Things the learner did correctly or "
            "demonstrated well."
        ),
    )

    weaknesses: list[str] = Field(
        default_factory=list,
        description=(
            "Important mistakes, misunderstandings, "
            "or missing concepts."
        ),
    )

    next_step: str = Field(
        description=(
            "The most useful next learning step for "
            "the learner."
        )
    )