from app.services.learning.adaptive_loop import (
    AdaptiveLearningService,
)
from app.db.database import SessionLocal


LEARNER_ID = "adaptive-loop-test-002"


def build_learner_answer(
    skill_id: str,
) -> str:

    # =====================================================
    # Simulated learner responses
    #
    # These are deliberately written to match the skill
    # selected by the recommender.
    # =====================================================

    if skill_id == "programming-fundamentals":

        return """
user_name = "Sameer"
user_age = 21
user_height = 5.9
is_enrolled = True

print(user_name, type(user_name))
print(user_age, type(user_age))
print(user_height, type(user_height))
print(is_enrolled, type(is_enrolled))
"""

    if skill_id == "fastapi":

        return """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float


@app.get("/")
def root():

    return {
        "message": "Welcome to FastAPI"
    }


@app.post("/items/")
def create_item(
    item: Item,
):

    tax = item.price * 0.10

    return {
        "name": item.name,
        "price": item.price,
        "tax": tax,
    }
"""

    if skill_id == "rest":

        return """
A REST API should use HTTP methods according to
the operation being performed.

GET is used to retrieve data.

POST is used to create a new resource.

PUT can replace an existing resource.

PATCH can partially update an existing resource.

DELETE removes a resource.
"""

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    return """
I completed the requested learning activity
and attempted all of the required steps.
"""


def main():

    db = SessionLocal()

    try:

        service = (
            AdaptiveLearningService(db)
        )

        # =================================================
        # STEP 1
        # RECOMMENDER + GEMINI ACTIVITY
        # =================================================

        print(
            "\n"
            + "=" * 70
        )

        print(
            "STEP 1 — GENERATE NEXT ACTIVITY"
        )

        print(
            "=" * 70
        )

        generated = (
            service.generate_next_activity(
                LEARNER_ID
            )
        )

        if generated is None:

            print(
                "\nNo learning activity available."
            )

            return

        recommendation = (
            generated.recommendation
        )

        activity = (
            generated.activity
        )

        skill = (
            recommendation.skill
        )

        print(
            "\nRecommended skill:"
        )
        print(
    "\nActivity ID:"
)

        print(
            f"  {generated.activity_id}"
        )

        print(
            f"  {skill.label}"
        )

        print(
            f"\nSkill ID:"
        )

        print(
            f"  {skill.id}"
        )

        print(
            f"\nRecommendation score:"
        )

        print(
            f"  {recommendation.score:.3f}"
        )

        print(
            f"\nRecommendation reason:"
        )

        print(
            f"  {recommendation.reason}"
        )

        print(
            "\nGenerated activity:"
        )

        print(
            f"  {activity.title}"
        )

        print(
            "\nActivity objective:"
        )

        print(
            f"  {activity.objective}"
        )

        print(
            "\nActivity difficulty:"
        )

        print(
            f"  {activity.difficulty}"
        )

        print(
            "\nActivity instructions:"
        )

        print(
            f"  {activity.instructions}"
        )

        # =================================================
        # STEP 2
        # SIMULATED LEARNER ANSWER
        # =================================================

        learner_answer = (
            build_learner_answer(
                skill.id
            )
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "STEP 2 — LEARNER SUBMITS ANSWER"
        )

        print(
            "=" * 70
        )

        print(
            "\nLearner answer:"
        )

        print(
            learner_answer
        )

        # =================================================
        # STEP 3
        # GEMINI EVALUATES
        # =================================================

        evaluation = service.evaluate_response(
            learner_id=LEARNER_ID,
            activity_id=generated.activity_id,
            learner_answer=learner_answer,
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "STEP 3 — GEMINI EVALUATION"
        )

        print(
            "=" * 70
        )

        print(
            f"\nScore:"
        )

        print(
            f"  "
            f"{evaluation.evaluation.score:.3f}"
        )

        print(
            f"\nCorrect:"
        )

        print(
            f"  "
            f"{evaluation.evaluation.correct}"
        )

        print(
            "\nFeedback:"
        )

        print(
            f"  "
            f"{evaluation.evaluation.feedback}"
        )

        print(
            "\nStrengths:"
        )

        for strength in (
            evaluation.evaluation.strengths
        ):

            print(
                f"  + {strength}"
            )

        print(
            "\nWeaknesses:"
        )

        for weakness in (
            evaluation.evaluation.weaknesses
        ):

            print(
                f"  - {weakness}"
            )

        print(
            "\nNext step:"
        )

        print(
            f"  "
            f"{evaluation.evaluation.next_step}"
        )

        # =================================================
        # STEP 4
        # UPDATED LEARNER STATE
        # =================================================

        state = (
            evaluation.feedback.state
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "STEP 4 — UPDATED LEARNER STATE"
        )

        print(
            "=" * 70
        )

        print(
            f"\nSkill:"
        )

        print(
            f"  {state.skill_id}"
        )

        print(
            f"\nMastery:"
        )

        print(
            f"  {state.mastery:.3f}"
        )

        print(
            f"\nTheta:"
        )

        print(
            f"  {state.theta:.3f}"
        )

        print(
            f"\nConfidence:"
        )

        print(
            f"  {state.confidence:.3f}"
        )

        print(
            f"\nAttempts:"
        )

        print(
            f"  {state.attempts}"
        )

        print(
            f"\nStatus:"
        )

        print(
            f"  {state.status}"
        )

        # =================================================
        # STEP 5
        # RECOMMEND AGAIN
        # =================================================

        print(
            "\n"
            + "=" * 70
        )

        print(
            "STEP 5 — NEXT RECOMMENDATION"
        )

        print(
            "=" * 70
        )

        next_result = (
            service.generate_next_activity(
                LEARNER_ID
            )
        )

        if next_result is None:

            print(
                "\nNo next recommendation available."
            )

            return

        next_recommendation = (
            next_result.recommendation
        )

        print(
            "\nNext recommended skill:"
        )

        print(
            f"  "
            f"{next_recommendation.skill.label}"
        )

        print(
            f"\nNext score:"
        )

        print(
            f"  "
            f"{next_recommendation.score:.3f}"
        )

        print(
            f"\nNext reason:"
        )

        print(
            f"  "
            f"{next_recommendation.reason}"
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "ADAPTIVE LOOP COMPLETE"
        )

        print(
            "=" * 70
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()