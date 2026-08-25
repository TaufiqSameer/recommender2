from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm.provider import (
    get_llm,
)

from app.ai.llm.prompts import (
    LEARNING_EVALUATION_SYSTEM_PROMPT,
    LEARNING_EVALUATION_USER_PROMPT,
)

from app.ai.llm.schemas import (
    LearningEvaluation,
)


class LearningEvaluationChain:

    def __init__(self):

        # -------------------------------------------------
        # Use the BASE LLM.
        #
        # Do NOT use get_learner_intent_llm().
        #
        # This chain needs its own structured output:
        # LearningEvaluation.
        # -------------------------------------------------

        self.llm = (
            get_llm()
            .with_structured_output(
                LearningEvaluation
            )
        )

        # -------------------------------------------------
        # Prompt
        # -------------------------------------------------

        self.prompt = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        LEARNING_EVALUATION_SYSTEM_PROMPT,
                    ),
                    (
                        "human",
                        LEARNING_EVALUATION_USER_PROMPT,
                    ),
                ]
            )
        )

        # -------------------------------------------------
        # Prompt → LLM
        # -------------------------------------------------

        self.chain = (
            self.prompt
            | self.llm
        )

    def invoke(
        self,
        *,
        skill: str,
        objective: str,
        activity: str,
        learner_answer: str,
    ) -> LearningEvaluation:

        """
        Evaluate a learner's answer to a generated
        learning activity.

        This method only performs evaluation.

        It does NOT:
        - update learner mastery
        - update theta
        - update confidence
        - create evidence
        - change recommendations
        """

        return self.chain.invoke(
            {
                "skill": skill,
                "objective": objective,
                "activity": activity,
                "learner_answer": learner_answer,
            }
        )