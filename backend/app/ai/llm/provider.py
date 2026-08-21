from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from app.ai.llm.schemas import LearnerIntent
from app.config import settings


def get_llm():
    if settings.llm_provider == "gemini":

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        return ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )

    if settings.llm_provider == "ollama":

        return ChatOllama(
            model=settings.ollama_model,
            temperature=0,
        )

    raise ValueError(
        f"Unsupported LLM provider: "
        f"{settings.llm_provider}"
    )


def get_learner_intent_llm():
    llm = get_llm()

    return llm.with_structured_output(
        LearnerIntent
    )