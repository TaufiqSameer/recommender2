from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm.provider import (
    get_learner_intent_llm,
)
from app.ai.llm.prompts import (
    LEARNER_INTENT_SYSTEM_PROMPT,
    LEARNER_INTENT_USER_PROMPT,
)
from app.ai.llm.schemas import LearnerIntent


class GoalUnderstandingChain:

    def __init__(self):

        self.llm = get_learner_intent_llm()

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    LEARNER_INTENT_SYSTEM_PROMPT,
                ),
                (
                    "human",
                    LEARNER_INTENT_USER_PROMPT,
                ),
            ]
        )

        self.chain = self.prompt | self.llm

    def invoke(
        self,
        message: str,
    ) -> LearnerIntent:

        return self.chain.invoke(
            {
                "message": message,
            }
        )