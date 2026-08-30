"""
Conversational onboarding service.

Manages the state machine:
  NEW → DISCOVERING_GOAL → DISCOVERING_INTERESTS →
  DISCOVERING_BACKGROUND → ASSESSMENT → PROFILE_READY → LEARNING

Gemini drives the conversation; the application owns the state.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.llm.provider import get_llm
from app.db.models.learner import LearnerProfile, LearnerSkillState
from app.db.models.assessment import Assessment, AssessmentQuestion, AssessmentAttempt, AssessmentAnswer
from app.db.models.skill import SkillNode
from app.db.models.learner import LearnerEvidence


# ─── Onboarding states ───────────────────────────────────────────────────────

ONBOARDING_STATES = [
    "NEW",
    "DISCOVERING_GOAL",
    "DISCOVERING_INTERESTS",
    "DISCOVERING_BACKGROUND",
    "ASSESSMENT",
    "PROFILE_READY",
    "LEARNING",
]


@dataclass
class OnboardingResponse:
    message: str
    state: str
    progress: int   # 0-100
    assessment_question: dict | None = None  # present during ASSESSMENT
    assessment_complete: bool = False


# ─── Prompts ─────────────────────────────────────────────────────────────────

_ONBOARDING_SYSTEM = """
You are LearnAI, a friendly adaptive learning assistant.
You are onboarding a new learner and gathering information to personalise their learning path.

Your current phase: {phase}

Rules:
- Be warm, encouraging, concise, and natural.
- Ask one question at a time.
- Do not repeat information already provided.
- Do not mention internal state machine names or technical schemas.
- If the learner gives a vague answer, ask one clarifying follow-up, then accept.
- When enough information has been gathered for the current phase, include a single line:
  PHASE_COMPLETE:{{"goal": "...", "interests": "...", "background": "...", "domain": "...", "ready_for_next": true}}
  followed by your friendly conversational transition message asking the next phase question.
- Only include keys relevant to the current phase in the JSON. Set "ready_for_next": true when confident to proceed.
- When not advancing, simply respond with your natural conversational message.
""".strip()

_ONBOARDING_USER = """
Onboarding phase: {phase}

Conversation so far:
{history}

Learner's latest message:
{message}

Current learner profile (what we know so far):
Goal: {goal}
Domain: {domain}
Background: {background}
""".strip()


class OnboardingService:

    def __init__(self, db: Session):
        self.db = db
        try:
            self.llm = get_llm()
            self.chain = (
                ChatPromptTemplate.from_messages([
                    ("system", _ONBOARDING_SYSTEM),
                    ("human", _ONBOARDING_USER),
                ])
                | self.llm
                | StrOutputParser()
            )
            self._llm_available = True
        except Exception:
            self._llm_available = False

    def _get_learner(self, learner_id: str) -> LearnerProfile | None:
        return self.db.get(LearnerProfile, learner_id)

    def _phase_label(self, state: str) -> str:
        labels = {
            "NEW": "introduction",
            "DISCOVERING_GOAL": "understanding the learner's goal",
            "DISCOVERING_INTERESTS": "understanding interests and motivation",
            "DISCOVERING_BACKGROUND": "understanding prior experience",
            "ASSESSMENT": "initial assessment",
            "PROFILE_READY": "ready to start learning",
            "LEARNING": "active learning",
        }
        return labels.get(state, state)

    def _next_state(self, current: str) -> str:
        idx = ONBOARDING_STATES.index(current)
        if idx < len(ONBOARDING_STATES) - 1:
            return ONBOARDING_STATES[idx + 1]
        return current

    def _progress(self, state: str) -> int:
        idx = ONBOARDING_STATES.index(state)
        return int((idx / (len(ONBOARDING_STATES) - 1)) * 100)

    def _transition_message(self, state: str, learner: LearnerProfile) -> str:
        domain = learner.domain or "your chosen domain"
        if state == "DISCOVERING_INTERESTS":
            return (
                f"That sounds like a great goal! To help shape your learning path in **{domain}**, "
                f"what specific topics, technologies, or projects are you most interested in exploring?"
            )
        elif state == "DISCOVERING_BACKGROUND":
            return (
                "Great! To help calibrate the pace and difficulty of your challenges, "
                "could you share a bit about your previous experience with programming or technical concepts?"
            )
        elif state == "ASSESSMENT":
            return "Let's do a quick 5-question baseline assessment to establish your starting mastery level!"
        elif state == "PROFILE_READY":
            return "Your profile and personalized roadmap are ready! Let's head to your dashboard."
        return "What would you like to focus on next?"

    def chat(
        self,
        learner_id: str,
        message: str,
        history: list[dict],
    ) -> OnboardingResponse:
        learner = self._get_learner(learner_id)
        if learner is None:
            return OnboardingResponse(
                message="Learner not found.",
                state="NEW",
                progress=0,
            )

        state = learner.onboarding_state

        # If already in LEARNING, bounce back
        if state == "LEARNING":
            return OnboardingResponse(
                message="You're all set! Head to the dashboard to start learning.",
                state="LEARNING",
                progress=100,
            )

        # Transition from NEW → DISCOVERING_GOAL on first message
        if state == "NEW":
            state = "DISCOVERING_GOAL"
            learner.onboarding_state = state
            self.db.commit()

        # --- LLM call ---
        if not self._llm_available:
            return OnboardingResponse(
                message=(
                    "LearnAI is temporarily unavailable. "
                    "Your progress is safe. Please try again in a moment."
                ),
                state=state,
                progress=self._progress(state),
            )

        history_text = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in history[-10:]
        ) or "No previous messages."

        try:
            raw = self.chain.invoke({
                "phase": self._phase_label(state),
                "history": history_text,
                "message": message,
                "goal": learner.goal or "Not yet provided",
                "domain": learner.domain or "Not yet provided",
                "background": (learner.preferences or {}).get("background", "Not yet provided"),
            })
        except Exception:
            return OnboardingResponse(
                message=(
                    "LearnAI is temporarily unavailable. "
                    "Your progress is safe. Please try again in a moment."
                ),
                state=state,
                progress=self._progress(state),
            )

        # Check if LLM wants to advance phase
        if "PHASE_COMPLETE:" in raw:
            try:
                match = re.search(r"PHASE_COMPLETE:\s*(\{.*?\})", raw, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    data = json.loads(json_str)

                    if data.get("ready_for_next"):
                        # Persist extracted info
                        if data.get("goal"):
                            learner.goal = data["goal"]
                        if data.get("domain"):
                            learner.domain = data["domain"]
                        if data.get("background"):
                            prefs = dict(learner.preferences or {})
                            prefs["background"] = data["background"]
                            learner.preferences = prefs
                        if data.get("interests"):
                            prefs = dict(learner.preferences or {})
                            prefs["interests"] = data["interests"]
                            learner.preferences = prefs

                        next_state = self._next_state(state)
                        learner.onboarding_state = next_state
                        self.db.commit()
                        state = next_state

                        # If entering ASSESSMENT, prepare questions
                        if state == "ASSESSMENT":
                            return self._start_assessment(learner)

                        if state == "PROFILE_READY":
                            return OnboardingResponse(
                                message=(
                                    "Great! I have everything I need. "
                                    "Your personalised learning path is ready. "
                                    "Let's get started!"
                                ),
                                state=state,
                                progress=self._progress(state),
                            )

                        # Clean any leftover text or generate natural transition
                        clean_text = re.sub(r"PHASE_COMPLETE:\s*\{.*?\}", "", raw, flags=re.DOTALL).strip()
                        clean_text = re.sub(r"^```[a-z]*\s*|```$", "", clean_text, flags=re.MULTILINE).strip()

                        if not clean_text:
                            clean_text = self._transition_message(state, learner)

                        return OnboardingResponse(
                            message=clean_text,
                            state=state,
                            progress=self._progress(state),
                        )

            except (json.JSONDecodeError, KeyError):
                pass  # Fall through to return cleaned message

        # Clean any accidental PHASE_COMPLETE markers from general message
        clean_raw = re.sub(r"PHASE_COMPLETE:\s*\{.*?\}", "", raw, flags=re.DOTALL).strip()
        clean_raw = re.sub(r"^```[a-z]*\s*|```$", "", clean_raw, flags=re.MULTILINE).strip()
        if not clean_raw:
            clean_raw = self._transition_message(state, learner)

        return OnboardingResponse(
            message=clean_raw,
            state=state,
            progress=self._progress(state),
        )

    def _start_assessment(self, learner: LearnerProfile) -> OnboardingResponse:
        """
        Find or create a 5-question initial assessment for the learner's domain.
        Returns the first question.
        """
        domain = learner.domain or "backend"

        # Find skills in the domain (or all available skills)
        skills = list(self.db.scalars(
            select(SkillNode).where(SkillNode.domain == domain).limit(5)
        ))

        if not skills:
            skills = list(self.db.scalars(select(SkillNode).limit(5)))

        if not skills:
            # No skills in DB at all — skip assessment
            learner.onboarding_state = "PROFILE_READY"
            self.db.commit()
            return OnboardingResponse(
                message=(
                    "I don't have a structured assessment ready yet, "
                    "but don't worry — I'll adapt your learning path as we go! "
                    "Let's head to your dashboard."
                ),
                state="PROFILE_READY",
                progress=self._progress("PROFILE_READY"),
            )

        # Check for existing assessment attempt
        existing_attempt = self.db.scalars(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.learner_id == learner.learner_id)
            .order_by(AssessmentAttempt.started_at.desc())
        ).first()

        synthetic_assessment_id = f"initial-{domain.lower().replace(' ', '-')}"

        # Ensure Assessment record exists in DB
        assessment = self.db.get(Assessment, synthetic_assessment_id)
        if assessment is None:
            assessment = Assessment(
                id=synthetic_assessment_id,
                skill_id=skills[0].id,
                title=f"Initial {domain.title()} Assessment",
                difficulty=1.5,
                generation_source="system",
            )
            self.db.add(assessment)
            self.db.flush()

        if existing_attempt and existing_attempt.completed_at is None:
            # Resume existing attempt
            attempt = existing_attempt
        else:
            attempt_id = str(uuid.uuid4())
            attempt = AssessmentAttempt(
                id=attempt_id,
                learner_id=learner.learner_id,
                assessment_id=synthetic_assessment_id,
                total_questions=min(5, len(skills)),
            )
            self.db.add(attempt)
            self.db.flush()

        # Ensure AssessmentQuestion records exist for all skills in this attempt
        for idx, skill in enumerate(skills[:attempt.total_questions]):
            qid = f"{attempt.id}-q{idx}"
            if not self.db.get(AssessmentQuestion, qid):
                q_data = self._build_question(skill, idx)
                q_record = AssessmentQuestion(
                    id=qid,
                    assessment_id=synthetic_assessment_id,
                    skill_id=skill.id,
                    question=q_data["question"],
                    question_type=q_data["question_type"],
                    question_data={},
                    correct_answer=skill.label,
                    difficulty=1.0 + (idx * 0.5),
                    discrimination=1.0,
                )
                self.db.add(q_record)

        self.db.commit()

        # Count answers given so far
        answers_given = list(self.db.scalars(
            select(AssessmentAnswer)
            .where(AssessmentAnswer.attempt_id == attempt.id)
        ))

        q_index = len(answers_given)
        total = attempt.total_questions

        if q_index >= total:
            return self._finish_assessment(learner, attempt, skills)

        # Generate question text for current skill
        skill = skills[q_index]
        question_data = self._build_question(skill, q_index)

        return OnboardingResponse(
            message=(
                f"Question {q_index + 1} of {total}:\n\n"
                f"{question_data['question']}"
            ),
            state="ASSESSMENT",
            progress=self._progress("ASSESSMENT"),
            assessment_question={
                "index": q_index,
                "total": total,
                "attempt_id": attempt.id,
                "skill_id": skill.id,
                "skill_label": skill.label,
                **question_data,
            },
        )

    def _build_question(self, skill: SkillNode, index: int) -> dict:
        """Build a simple question dict for a skill."""
        difficulty_levels = ["beginner", "beginner", "intermediate", "intermediate", "advanced"]
        difficulty = difficulty_levels[min(index, 4)]

        return {
            "question": (
                f"To assess your knowledge of **{skill.label}**, "
                f"please answer this {difficulty}-level question:\n\n"
                f"{skill.description}\n\n"
                f"In your own words, explain this concept and give a brief example."
            ),
            "question_type": "short_answer",
            "difficulty": difficulty,
            "skill_label": skill.label,
        }

    def submit_assessment_answer(
        self,
        learner_id: str,
        attempt_id: str,
        answer: str,
    ) -> OnboardingResponse:
        """Score an assessment answer and advance to the next question."""
        learner = self._get_learner(learner_id)
        attempt = self.db.get(AssessmentAttempt, attempt_id)

        if not learner or not attempt:
            return OnboardingResponse(
                message="Assessment not found.",
                state="ASSESSMENT",
                progress=self._progress("ASSESSMENT"),
            )

        domain = learner.domain or "backend"
        skills = list(self.db.scalars(
            select(SkillNode).where(SkillNode.domain == domain).limit(5)
        ))
        if not skills:
            skills = list(self.db.scalars(select(SkillNode).limit(5)))

        answers_given = list(self.db.scalars(
            select(AssessmentAnswer)
            .where(AssessmentAnswer.attempt_id == attempt_id)
        ))

        q_index = len(answers_given)

        # Score the answer heuristically (word count as proxy)
        score = min(1.0, len(answer.split()) / 30)
        correct = score >= 0.4

        if q_index < len(skills):
            skill = skills[q_index]
            qid = f"{attempt_id}-q{q_index}"

            # Guarantee AssessmentQuestion exists in DB before inserting AssessmentAnswer
            q_record = self.db.get(AssessmentQuestion, qid)
            if not q_record:
                q_data = self._build_question(skill, q_index)
                q_record = AssessmentQuestion(
                    id=qid,
                    assessment_id=attempt.assessment_id,
                    skill_id=skill.id,
                    question=q_data["question"],
                    question_type=q_data["question_type"],
                    question_data={},
                    correct_answer=skill.label,
                    difficulty=1.0 + (q_index * 0.5),
                    discrimination=1.0,
                )
                self.db.add(q_record)
                self.db.flush()

            answer_record = AssessmentAnswer(
                id=str(uuid.uuid4()),
                attempt_id=attempt_id,
                question_id=qid,
                answer=answer,
                correct=correct,
                score=score,
            )
            self.db.add(answer_record)

            # Record evidence
            evidence = LearnerEvidence(
                learner_id=learner_id,
                skill_id=skill.id,
                evidence_type="initial_assessment",
                source_id=attempt_id,
                score=score,
                evidence_metadata={
                    "question_index": q_index,
                    "correct": correct,
                    "difficulty": ["beginner", "beginner", "intermediate", "intermediate", "advanced"][min(q_index, 4)],
                },
            )
            self.db.add(evidence)

            attempt.correct_answers += (1 if correct else 0)

            # Update learner skill state
            state = self.db.scalars(
                select(LearnerSkillState)
                .where(
                    LearnerSkillState.learner_id == learner_id,
                    LearnerSkillState.skill_id == skill.id,
                )
            ).first()

            if state is None:
                state = LearnerSkillState(
                    learner_id=learner_id,
                    skill_id=skill.id,
                    mastery=score * 0.5,
                    confidence=0.3,
                    status="available" if score > 0.3 else "learning",
                    attempts=1,
                )
                self.db.add(state)
            else:
                state.mastery = min(1.0, state.mastery + score * 0.2)
                state.attempts += 1

            self.db.commit()

        # Check if assessment is done
        total = attempt.total_questions
        new_answers = len(answers_given) + 1

        if new_answers >= total:
            return self._finish_assessment(learner, attempt, skills)

        # Next question
        next_index = new_answers
        if next_index < len(skills):
            skill = skills[next_index]
            q_data = self._build_question(skill, next_index)
            feedback = "Good answer! " if correct else "Thanks for your answer. "
            return OnboardingResponse(
                message=(
                    f"{feedback}\n\nQuestion {next_index + 1} of {total}:\n\n"
                    f"{q_data['question']}"
                ),
                state="ASSESSMENT",
                progress=self._progress("ASSESSMENT"),
                assessment_question={
                    "index": next_index,
                    "total": total,
                    "attempt_id": attempt_id,
                    "skill_id": skill.id,
                    "skill_label": skill.label,
                    **q_data,
                },
            )

        return self._finish_assessment(learner, attempt, skills)

    def _finish_assessment(
        self,
        learner: LearnerProfile,
        attempt: AssessmentAttempt,
        skills: list,
    ) -> OnboardingResponse:
        import datetime as dt
        attempt.completed_at = dt.datetime.utcnow()
        attempt.score = (
            attempt.correct_answers / attempt.total_questions
            if attempt.total_questions > 0
            else 0.0
        )
        learner.onboarding_state = "PROFILE_READY"
        self.db.commit()

        level = (
            "advanced" if attempt.score > 0.7
            else "intermediate" if attempt.score > 0.4
            else "beginner"
        )

        return OnboardingResponse(
            message=(
                f"Assessment complete! Based on your answers, "
                f"you appear to be at a **{level}** level. "
                f"I've set up your personalised learning path. "
                f"Let's go to your dashboard!"
            ),
            state="PROFILE_READY",
            progress=self._progress("PROFILE_READY"),
            assessment_complete=True,
        )

    def complete_onboarding(self, learner_id: str) -> None:
        """Mark learner as ready to learn."""
        learner = self._get_learner(learner_id)
        if learner:
            learner.onboarding_state = "LEARNING"
            self.db.commit()
