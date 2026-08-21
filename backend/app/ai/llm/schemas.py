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