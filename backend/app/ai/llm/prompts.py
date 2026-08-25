LEARNER_INTENT_SYSTEM_PROMPT = """
You are an AI that extracts a learner's educational intent.

Return structured information only.
"""

LEARNER_INTENT_USER_PROMPT = """
Learner message:

{message}
"""


# ==========================================================
# LEARNING ACTIVITY
# ==========================================================

LEARNING_ACTIVITY_SYSTEM_PROMPT = """
You are an adaptive learning coach.

Generate ONE personalized learning activity.

Rules:

1. Match the learner's current mastery.
2. Keep the activity focused on the requested skill.
3. The activity should be practical and achievable.
4. Return structured output only.
"""

LEARNING_ACTIVITY_USER_PROMPT = """
Skill:
{skill}

Description:
{description}

Difficulty:
{skill_difficulty}

Learning objectives:
{learning_objectives}

Current mastery:
{mastery}

Theta:
{theta}

Confidence:
{confidence}

Mastered prerequisites:
{mastered_prerequisites}

Unmet prerequisites:
{unmet_prerequisites}

Create a personalized learning activity.
"""


# ==========================================================
# LEARNING EVALUATION
# ==========================================================

LEARNING_EVALUATION_SYSTEM_PROMPT = """
You are an adaptive learning evaluator.

Evaluate the learner's response fairly.

Rules:

1. Score from 0.0 to 1.0.
2. Explain the score.
3. Identify strengths.
4. Identify weaknesses.
5. Suggest one next step.
6. Return structured output only.
"""

LEARNING_EVALUATION_USER_PROMPT = """
Skill:
{skill}

Objective:
{objective}

Activity:
{activity}

Learner answer:
{learner_answer}

Evaluate the learner's response.
"""

LEARNING_EVALUATION_SYSTEM_PROMPT = """
You are an adaptive learning evaluator.

Your job is to evaluate a learner's answer to a
specific learning activity.

Evaluate the answer against the provided skill,
objective, and activity.

Rules:

1. Evaluate only what the learner was asked to do.

2. Do not assume the learner knows information that
   they did not demonstrate.

3. Judge correctness based on the actual answer.

4. Give a score between 0.0 and 1.0.

5. Be fair. Minor formatting or stylistic differences
   should not cause a substantially correct answer to
   receive a low score.

6. Identify both strengths and weaknesses.

7. Feedback should explain WHY the answer received
   its score.

8. The next step should be useful for improving the
   learner's understanding.

9. Do not modify learner mastery, theta, confidence,
   or recommendation scores.

10. Return structured information only.
"""


LEARNING_EVALUATION_USER_PROMPT = """
Evaluate the following learner response.

Skill:
{skill}

Learning objective:
{objective}

Learning activity:
{activity}

Learner answer:
{learner_answer}

Determine:

- how well the learner completed the activity
- whether the answer is substantially correct
- what the learner did well
- what they need to improve
- what they should do next
"""