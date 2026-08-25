from langchain_core.prompts import ChatPromptTemplate
from typing import cast
from app.ai.llm.provider import (
    get_llm,
)

from app.ai.llm.prompts import (
    LEARNING_ACTIVITY_SYSTEM_PROMPT,
    LEARNING_ACTIVITY_USER_PROMPT,
)

from app.ai.llm.schemas import (
    LearningActivity,
)


class LearningActivityChain:

    def __init__(self):

        self.llm = (
            get_llm()
            .with_structured_output(
                LearningActivity
            )
        )

        self.prompt = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        LEARNING_ACTIVITY_SYSTEM_PROMPT,
                    ),
                    (
                        "human",
                        LEARNING_ACTIVITY_USER_PROMPT,
                    ),
                ]
            )
        )

        self.chain = (
            self.prompt
            | self.llm
        )

    def invoke(
        self,
        *,
        skill: str,
        description: str,
        skill_difficulty: str,
        learning_objectives: list[str],
        mastery: float,
        theta: float,
        confidence: float,
        mastered_prerequisites: list[str],
        unmet_prerequisites: list[str],
    ) -> LearningActivity:

        result = self.chain.invoke(
            {
                "skill": skill,
                "description": description,
                "skill_difficulty": skill_difficulty,
                "learning_objectives": (
                    learning_objectives
                ),
                "mastery": mastery,
                "theta": theta,
                "confidence": confidence,
                "mastered_prerequisites": (
                    mastered_prerequisites
                ),
                "unmet_prerequisites": (
                    unmet_prerequisites
                ),
            }
        )

        return cast(
            LearningActivity,
            result,
        )