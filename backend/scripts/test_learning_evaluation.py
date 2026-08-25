from app.ai.chains.learning_evaluation import (
    LearningEvaluationChain,
)


def main():

    chain = LearningEvaluationChain()

    # =====================================================
    # The activity Gemini previously generated
    # =====================================================

    skill = "FastAPI"

    objective = (
        "Create a basic FastAPI application with "
        "a GET root endpoint and a POST endpoint "
        "that uses a Pydantic schema to validate input."
    )

    activity = """
Create a basic FastAPI application.

1. Import FastAPI from fastapi and BaseModel
   from pydantic.

2. Initialize a FastAPI app instance named 'app'.

3. Create a GET endpoint at '/' that returns:
   {'message': 'Welcome to FastAPI'}

4. Define a Pydantic model named 'Item' with:
   - name: string
   - price: float

5. Create a POST endpoint at '/items/' that accepts
   an Item payload.

6. Return the item details and calculate a tax
   equal to 10 percent of the price.
"""

    # =====================================================
    # Simulated learner answer
    #
    # This answer intentionally gets some things right
    # and misses the tax calculation.
    # =====================================================

    learner_answer = """
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
def create_item(item: Item):
    return {
        "name": item.name,
        "price": item.price
    }
"""

    # =====================================================
    # Ask Gemini to evaluate the learner
    # =====================================================

    evaluation = chain.invoke(
        skill=skill,
        objective=objective,
        activity=activity,
        learner_answer=learner_answer,
    )

    # =====================================================
    # Display evaluation
    # =====================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "GEMINI LEARNING EVALUATION"
    )

    print(
        "=" * 70
    )

    print(
        f"\nScore:"
        f"\n  {evaluation.score:.3f}"
    )

    print(
        f"\nCorrect:"
        f"\n  {evaluation.correct}"
    )

    print(
        f"\nFeedback:"
        f"\n  {evaluation.feedback}"
    )

    print(
        "\nStrengths:"
    )

    if not evaluation.strengths:

        print(
            "  None identified."
        )

    else:

        for index, strength in enumerate(
            evaluation.strengths,
            start=1,
        ):

            print(
                f"  {index}. {strength}"
            )

    print(
        "\nWeaknesses:"
    )

    if not evaluation.weaknesses:

        print(
            "  None identified."
        )

    else:

        for index, weakness in enumerate(
            evaluation.weaknesses,
            start=1,
        ):

            print(
                f"  {index}. {weakness}"
            )

    print(
        f"\nNext Step:"
        f"\n  {evaluation.next_step}"
    )

    print(
        "\n"
        + "=" * 70
    )


if __name__ == "__main__":
    main()