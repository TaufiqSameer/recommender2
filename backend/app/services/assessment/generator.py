from typing import Literal

from google import genai
from pydantic import BaseModel, Field

from app.config import settings


class GeneratedQuestion(BaseModel):
    question: str

    question_type: Literal[
        "multiple_choice",
        "true_false",
        "short_answer",
    ]

    options: list[str] = Field(
        default_factory=list,
    )

    correct_answer: str

    explanation: str

    difficulty: float = Field(
        ge=1.0,
        le=5.0,
    )


class GeneratedAssessment(BaseModel):
    title: str
    description: str

    questions: list[GeneratedQuestion]


class AssessmentGenerator:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def generate(
        self,
        skill_name: str,
        skill_description: str | None = None,
        difficulty: float = 2.0,
        num_questions: int = 5,
    ) -> GeneratedAssessment:

        prompt = f"""
You are an assessment designer for an adaptive
learning platform.

Create a diagnostic assessment for the skill:

Skill: {skill_name}

Skill description:
{skill_description or "No description provided."}

Target difficulty:
{difficulty}

Number of questions:
{num_questions}

The purpose of this assessment is to estimate the
learner's actual knowledge of the skill.

Requirements:

1. Questions must directly test the specified skill.

2. Questions should cover different aspects of the
   skill rather than repeatedly testing the same fact.

3. Questions should range around the requested
   difficulty.

4. Avoid trivia and questions that can be answered
   without understanding the skill.

5. Prefer practical and conceptual questions.

6. For multiple-choice questions:
   - provide 3-4 options
   - provide exactly one correct answer

7. For true/false questions:
   - provide exactly two options:
     True
     False

8. For short-answer questions:
   - options should be empty
   - provide a concise expected answer

9. Every question must include:
   - question
   - question_type
   - options
   - correct_answer
   - explanation
   - difficulty

10. The correct answer must be explicitly included
    in the generated structure.

11. Do not create questions about prerequisites
    unless they are directly relevant to assessing
    the requested skill.

Return only the structured assessment.
"""

        response = self.client.models.generate_content(
            model=settings.google_model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": GeneratedAssessment,
            },
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty assessment."
            )

        return GeneratedAssessment.model_validate_json(
            response.text
        )