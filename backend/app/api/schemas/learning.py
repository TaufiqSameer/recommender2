from pydantic import BaseModel, Field


class ActivitySubmission(BaseModel):

    answer: str = Field(
        min_length=1,
        description=(
            "The learner's answer to the "
            "learning activity."
        ),
    )