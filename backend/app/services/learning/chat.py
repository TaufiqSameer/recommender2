from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.learning_chat import (
    LearningChatChain,
)

from app.db.models import (
    LearnerEvidence,
    LearnerSkillState,
    LearningActivity,
    SkillNode,
)


@dataclass
class LearningChatResult:

    message: str

    skill_id: str | None

    mastery: float | None

    confidence: float | None


class LearningChatService:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

        self.chat_chain = (
            LearningChatChain()
        )


    def respond(
        self,
        *,
        learner_id: str,
        message: str,
        activity_id: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> LearningChatResult:

        # =================================================
        # 1. Find the current activity
        # =================================================

        activity = None

        if activity_id:

            activity = (
                self.db.scalars(
                    select(
                        LearningActivity
                    )
                    .where(
                        LearningActivity.id
                        == activity_id,

                        LearningActivity.learner_id
                        == learner_id,
                    )
                )
                .first()
            )


        # =================================================
        # 2. If no activity was supplied,
        #    use the learner's latest activity.
        # =================================================

        if activity is None:

            activity = (
                self.db.scalars(
                    select(
                        LearningActivity
                    )
                    .where(
                        LearningActivity.learner_id
                        == learner_id
                    )
                    .order_by(
                        LearningActivity.created_at.desc()
                    )
                )
                .first()
            )


        # =================================================
        # 3. Determine current skill
        # =================================================

        skill = None

        if activity is not None:

            skill = self.db.get(
                SkillNode,
                activity.skill_id,
            )


        # =================================================
        # 4. Determine learner state
        # =================================================

        state = None

        if activity is not None:

            state = (
                self.db.scalars(
                    select(
                        LearnerSkillState
                    )
                    .where(
                        LearnerSkillState.learner_id
                        == learner_id,

                        LearnerSkillState.skill_id
                        == activity.skill_id,
                    )
                )
                .first()
            )


        # =================================================
        # 5. Safe defaults
        # =================================================

        mastery = (
            state.mastery
            if state is not None
            else 0.0
        )

        confidence = (
            state.confidence
            if state is not None
            else 0.0
        )

        skill_label = (
            skill.label
            if skill is not None
            else "Unknown"
        )


        # =================================================
        # 6. Build authoritative activity context
        # =================================================

        if activity is None:

            activity_context = """
CURRENT ACTIVITY

No current learning activity is available.

There are no activity-specific requirements to follow.
Answer the learner's question normally while keeping
the response educational and appropriate to their
current skill level.
""".strip()

        else:

            activity_context = f"""
CURRENT LEARNING ACTIVITY

Title:
{activity.title}

Type:
{activity.activity_type}

Objective:
{activity.objective}

Difficulty:
{activity.difficulty}

INSTRUCTIONS:
{activity.instructions}


IMPORTANT ACTIVITY RULES

The instructions above are the authoritative requirements
for the current learning activity.

When the learner asks about this activity:

1. Treat the activity instructions as the source of truth.

2. Do not contradict the activity instructions.

3. Do not suggest an alternative solution that violates
   the activity requirements.

4. If the learner misunderstands a requirement, explain
   why the stated requirement exists.

5. Help the learner understand and solve the activity,
   rather than silently changing the problem.

6. You may explain concepts using additional examples,
   but those examples must remain consistent with the
   activity requirements.

7. Do not remove, weaken, or reinterpret explicit
   conditions from the activity.

8. Prefer guiding the learner rather than immediately
   giving the complete answer unless the learner
   explicitly asks for the solution.
""".strip()


        # =================================================
        # 7. Get recent learner evidence
        # =================================================

        evidence = list(
            self.db.scalars(
                select(
                    LearnerEvidence
                )
                .where(
                    LearnerEvidence.learner_id
                    == learner_id
                )
                .order_by(
                    LearnerEvidence.created_at.desc()
                )
                .limit(5)
            )
        )


        if not evidence:

            recent_evidence = (
                "No previous learning evidence "
                "is available."
            )

        else:

            evidence_lines = []

            for item in evidence:

                evidence_lines.append(
                    (
                        f"skill={item.skill_id}, "
                        f"type={item.evidence_type}, "
                        f"score={item.score}, "
                        f"metadata={item.evidence_metadata}"
                    )
                )

            recent_evidence = "\n".join(
                evidence_lines
            )


        # =================================================
        # 8. Format conversation history
        # =================================================

        if not conversation_history:

            history_text = (
                "No previous conversation."
            )

        else:

            history_lines = []

            for item in conversation_history[-12:]:

                role = item.get(
                    "role",
                    "user",
                )

                content = item.get(
                    "content",
                    "",
                )

                # Prevent malformed history entries
                # from producing useless prompt content.

                if not content.strip():
                    continue

                history_lines.append(
                    f"{role}: {content}"
                )


            history_text = (
                "\n".join(history_lines)
                if history_lines
                else "No previous conversation."
            )


        # =================================================
        # 9. Ask Gemini (with graceful resilience fallback)
        # =================================================

        try:
            response = self.chat_chain.invoke(
                learner_id=learner_id,
                skill=skill_label,
                mastery=mastery,
                confidence=confidence,
                activity=activity_context,
                recent_evidence=recent_evidence,
                conversation_history=history_text,
                message=message,
            )
        except Exception:
            if activity is not None:
                response = (
                    f"Here is some guidance on **{skill_label}**: "
                    f"Focus on the main requirement in the instructions: \"{activity.instructions[:150]}...\". "
                    f"Break the solution down step-by-step and write clean, direct code or explanation."
                )
            else:
                response = (
                    f"I'm here to help you master **{skill_label}**. "
                    f"Try breaking your question or exercise down into core concepts and let's tackle it step by step!"
                )


        # =================================================
        # 10. Return tutor response
        # =================================================

        return LearningChatResult(
            message=response,

            skill_id=(
                activity.skill_id
                if activity is not None
                else None
            ),

            mastery=(
                mastery
                if state is not None
                else None
            ),

            confidence=(
                confidence
                if state is not None
                else None
            ),
        )