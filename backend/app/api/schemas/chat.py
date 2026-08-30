from pydantic import BaseModel, Field


class ChatMessage(BaseModel):

    role: str = Field(
        description=(
            "Message role: user or assistant."
        )
    )

    content: str = Field(
        description=(
            "Message content."
        )
    )


class LearningChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        description=(
            "The learner's message."
        ),
    )

    activity_id: str | None = Field(
        default=None,
        description=(
            "Optional current learning activity ID."
        ),
    )

    conversation_history: list[
        ChatMessage
    ] = Field(
        default_factory=list,
        description=(
            "Recent conversation messages."
        ),
    )