import json
from typing import Literal

from google import genai
from pydantic import BaseModel, Field

from app.config import settings


class Relationship(BaseModel):
    type: Literal[
        "requires",
        "background",
        "related_to",
    ]

    target: str

    strength: Literal[
        "hard",
        "background",
        "related",
    ]


class ResearchResult(BaseModel):
    concept: str
    domain: str
    description: str

    proposed_relationships: list[Relationship]

    sources: list[str]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class KnowledgeResearcher:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def research(
        self,
        concept: str,
        domain: str | None = None,
    ) -> ResearchResult:

        prompt = f"""
You are a knowledge researcher for an adaptive
learning platform.

Research the following concept:

Concept: {concept}
Domain: {domain or "general"}

Your job is to produce accurate knowledge that can
be used to build a prerequisite-aware learning graph.

Return:

1. A concise description of the concept.
2. A small number of meaningful relationships.
3. Reliable supporting sources.
4. A confidence score between 0 and 1.

RELATIONSHIP TYPES

"requires"
    The target is genuinely required before a learner
    can meaningfully learn or use this concept.

"background"
    The target is useful supporting knowledge but
    should NOT block the learner from starting this
    concept.

"related_to"
    The target is related to the concept but is not
    a prerequisite.

RELATIONSHIP STRENGTH

"hard"
    A genuine prerequisite that should participate
    in the prerequisite graph.

"background"
    Useful knowledge but should NOT block learning.

"related"
    Related information only.

IMPORTANT RULES

- Only classify something as "hard" if it is a genuine
  prerequisite.
- Do NOT turn every theoretically useful concept into
  a prerequisite.
- Avoid unnecessarily deep prerequisite chains.
- Prefer a small number of meaningful relationships.
- Do not invent URLs.
- Sources should be real and directly relevant.
- If you are uncertain about a relationship, prefer
  "background" or "related" instead of "hard".

For example, when researching a programming framework,
do not automatically make these hard prerequisites:

- Computer Architecture
- Binary Mathematics
- Operating Systems
- Advanced Mathematics

unless they are genuinely required for learning
the concept.

Return ONLY the requested structured data.
"""

        response = self.client.models.generate_content(
            model=settings.google_model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ResearchResult,
            },
        )

        text = response.text.strip()

        # -----------------------------------------
        # Handle accidental markdown fences
        # -----------------------------------------

        if text.startswith("```"):

            text = text.replace(
                "```json",
                "",
            )

            text = text.replace(
                "```",
                "",
            )

            text = text.strip()

        # -----------------------------------------
        # Parse JSON
        # -----------------------------------------

        try:

            data = json.loads(text)

        except json.JSONDecodeError as error:

            raise ValueError(
                "Gemini returned invalid JSON "
                f"for concept '{concept}'."
            ) from error

        # -----------------------------------------
        # Validate Gemini's entire response
        # -----------------------------------------

        try:

            return ResearchResult.model_validate(
                data
            )

        except Exception as error:

            raise ValueError(
                "Gemini returned an invalid research "
                f"structure for '{concept}'.\n"
                f"Response: {data}"
            ) from error