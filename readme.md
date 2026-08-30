# LearnAI — Master Vibe-Coding Prompt & Project Handoff

## 1. Project goal

LearnAI is an **AI-powered adaptive learning platform**.

The intended experience is:

```text
Learner
  ↓
Tell LearnAI what they want to learn
  ↓
Understand goals + interests + background
  ↓
Initial assessment
  ↓
Learner model
  ↓
Adaptive recommendation
  ↓
Learning activity
  ↓
Chat with LearnAI
  ↓
Submit work
  ↓
AI evaluation
  ↓
Evidence
  ↓
Updated mastery
  ↓
Next recommendation
```

The goal is to finish the existing project without throwing away the working backend or frontend.

---

# 2. What we have already built

## Backend

The backend is a **FastAPI + SQLAlchemy** application with an `app/` structure containing areas such as:

```text
app/
├── api/
├── ai/
├── config/
├── db/
├── services/
└── ...
```

Existing concepts include:

- Learners
- Skill nodes
- Learner skill state
- Learner evidence
- Learning activities
- Adaptive recommendation logic
- AI activity generation
- AI activity evaluation
- Learning feedback
- Conversational learning tutor
- Database layer
- Gemini/LangChain integration

---

# 3. Adaptive loop

The core adaptive system already exists.

Conceptually:

```text
Learner
   ↓
Learner Skill State
   ↓
Recommendation
   ↓
Learning Activity
   ↓
Attempt
   ↓
Evaluation
   ↓
Evidence
   ↓
Learner Model Update
   ↓
New Recommendation
   ↓
Next Activity
```

The learner state includes concepts such as:

```text
mastery
theta
confidence
attempts
status
last_assessed_at
```

The feedback system has already demonstrated that successful activity evaluation can change mastery, e.g. approximately `0.39 → 0.57`.

**Preserve this system. Do not replace it.**

---

# 4. Activities and evaluation

The system already generates learning activities with fields such as:

```text
activity_id
skill_id
title
type
objective
difficulty
instructions
hints
recommendation_score
generation_source
created_at
```

Activity submissions are evaluated and can return:

```text
score
correct
feedback
strengths
weaknesses
next_step
learner_state
```

This is already connected to evidence and learner-model updates.

---

# 5. Conversational tutor

A ChatGPT-like Learn page already exists.

It has:

- assistant/user messages
- activity card
- instructions
- hints
- activity answer area
- activity submission
- conversational chat composer
- mastery display
- loading/error states

The chat API is conceptually:

```text
POST /api/learners/{learner_id}/chat
```

Request:

```json
{
  "message": "...",
  "activity_id": "...",
  "conversation_history": []
}
```

Response:

```json
{
  "message": "...",
  "context": {
    "skill_id": "...",
    "mastery": 0.57,
    "confidence": 0.8
  }
}
```

The frontend already has API functions such as:

```text
getLearnerState()
getNextActivity()
getActivityHistory()
submitActivity()
sendLearningChat()
```

Do not scatter raw fetch calls throughout components.

---

# 6. Current chatbot grounding requirement

The tutor must be grounded in the current activity.

The activity instructions are authoritative.

For example, if the activity requires:

```text
age < 0
→ Invalid Age

age >= 18
→ Access Granted

otherwise
→ Access Denied
```

the tutor must not tell the learner that the negative-age condition is unnecessary.

Tutor behavior should:

- use the current activity
- respect explicit requirements
- use learner mastery/confidence
- use recent evidence
- use conversation history
- teach rather than always give answers
- provide useful hints
- adapt explanations to ability
- never silently modify the exercise

The `LearningChatService` and `LearningChatChain` should preserve this behavior.

---

# 7. Gemini quota resilience

Gemini has temporarily hit the free-tier request quota.

Observed error:

```text
429 RESOURCE_EXHAUSTED
generate_content_free_tier_requests
limit: 20
```

Do not redesign the project because of this.

Make the application resilient.

For activity generation:

```text
Suitable existing activity?
  ├─ YES → return it
  └─ NO  → generate with Gemini
```

Do not call Gemini unnecessarily on every GET.

For chat:

```text
Gemini available
  → normal response

Gemini unavailable
  → friendly fallback response
```

Never expose raw provider stack traces to the learner.

---

# 8. Current frontend

The frontend is:

```text
React
TypeScript
Vite
```

Already installed:

```text
react-router-dom
lucide-react
```

Existing routes include the dashboard and Learn experience.

The initial visual direction was whitish-blue. The final product should now use a polished **dark-purple theme**.

---

# 9. What remains

The major missing pieces are:

```text
1. User authentication
2. User → Learner relationship
3. Signup/login UI
4. Replace hardcoded learner ID
5. New learner conversational onboarding
6. Five-question initial assessment
7. Persistent conversations
8. Progress analytics
9. Real charts
10. Skill DAG / roadmap
11. Three.js visualization
12. Activity history
13. Profile/settings
14. Final dashboard polish
15. Responsive design
16. Error/loading/empty states
17. Full integration testing
18. Deployment
```

---

# 10. USER AUTHENTICATION

Build real authentication.

Create a `User` model with approximately:

```text
id
email
username
password_hash
is_active
created_at
updated_at
```

Use secure password hashing.

Use JWT authentication.

Endpoints:

```text
POST /api/auth/signup
POST /api/auth/login
GET  /api/auth/me
```

Frontend routes:

```text
/login
/signup
```

Signup flow:

```text
Signup
  ↓
Create User
  ↓
Create Learner profile
  ↓
Authenticate
  ↓
Dashboard
```

Login flow:

```text
Login
  ↓
Verify password
  ↓
Issue JWT
  ↓
Authenticated frontend state
  ↓
Dashboard
```

Do not keep using:

```text
adaptive-loop-test-002
```

as the production learner ID.

---

# 11. User vs Learner

Keep authentication and learning state separate.

Recommended:

```text
User
  │
  │ 1:1
  ↓
Learner
  │
  ├── LearnerSkillState
  ├── LearnerEvidence
  ├── LearningActivity
  ├── ActivityAttempt
  └── ChatSession
```

Meaning:

```text
User
→ Who is this?

Learner
→ What does this person know?
```

The backend should derive the learner from the authenticated user.

Do not trust an arbitrary learner ID supplied by the frontend for authorization.

---

# 12. Database additions

Preserve existing tables and add what is required.

Target data model:

```text
users
learners
skill_nodes
learner_skill_states
learner_evidence
learning_activities
assessment_attempts
assessment_answers
chat_sessions
chat_messages
```

Use migrations.

If Alembic is available, use Alembic.

Do not casually delete or recreate the database.

---

# 13. New-user conversational onboarding

Do not make onboarding a boring form unless required.

Use LearnAI as the entry point.

Example:

```text
LearnAI:
Hi! I'm LearnAI. What would you like to learn?

Learner:
I want to learn blockchain development.

LearnAI:
Nice. What are you hoping to do with blockchain?

Learner:
Build dApps and get a blockchain developer job.

LearnAI:
Got it. How comfortable are you with programming?

Learner:
I'm comfortable with Python but have never used Solidity.
```

The system should extract:

```text
goal
interests
background
experience
target
```

The chatbot can communicate naturally, but the application should own onboarding state.

---

# 14. Onboarding state machine

Implement explicit state:

```text
NEW
 ↓
DISCOVERING_GOAL
 ↓
DISCOVERING_INTERESTS
 ↓
DISCOVERING_BACKGROUND
 ↓
ASSESSMENT
 ↓
PROFILE_READY
 ↓
LEARNING
```

Store this state in the backend.

Do not make Gemini solely responsible for remembering the current onboarding phase.

---

# 15. Five-question assessment

After understanding the learner, ask approximately five questions.

Questions should depend on the learner's chosen domain.

Examples:

Python:

```text
Variables
Conditions
Loops
Functions
Data structures
```

Blockchain:

```text
Blockchain fundamentals
Transactions
Wallets/keys
Smart contracts
dApp architecture
```

Questions should provide objective evidence.

Use varying difficulty where useful:

```text
Beginner
Beginner
Intermediate
Intermediate
Advanced
```

---

# 16. Initial learner model

Assessment results should flow through the existing evidence system:

```text
Five answers
  ↓
Assessment results
  ↓
LearnerEvidence
  ↓
LearnerModelService
  ↓
Initial mastery
  ↓
Adaptive recommendation
```

Do not let Gemini arbitrarily invent mastery.

Store question-level evidence where practical:

```text
learner_id
skill_id
question_id
difficulty
correct
score
```

---

# 17. Persistent chat

Currently chat is held in React state.

Create:

```text
chat_sessions
chat_messages
```

Suggested structures:

```text
ChatSession
------------
id
learner_id
title
created_at
updated_at
```

```text
ChatMessage
-----------
id
session_id
role
content
created_at
```

Possible APIs:

```text
POST /api/chat/sessions
GET  /api/chat/sessions
GET  /api/chat/sessions/{id}
POST /api/chat/sessions/{id}/messages
```

After refresh, the conversation should remain available.

---

# 18. Progress page

Create:

```text
/progress
```

Display:

```text
Overall mastery
Skills mastered
Skills learning
Activities completed
Current streak
```

Use real database data.

Do not fabricate analytics.

Recommended charts:

### Mastery over time

Line chart:

```text
X = date
Y = mastery
```

### Skill mastery

Horizontal bar chart:

```text
Skill → mastery
```

### Activity performance

Show scores over time.

Keep the page readable. Do not add charts just for decoration.

---

# 19. Skill DAG / 3D learning graph

This is a major visual feature.

Use:

```bash
npm install three @react-three/fiber @react-three/drei
```

Represent actual skill dependencies.

Example:

```text
Programming Fundamentals
          │
          ├───────────────┐
          ↓               ↓
     Data Types       Control Flow
          │               │
          └──────┬────────┘
                 ↓
             Functions
                 ↓
          Data Structures
                 ↓
             Algorithms
```

Backend graph response:

```json
{
  "nodes": [
    {
      "id": "programming",
      "label": "Programming Fundamentals",
      "mastery": 0.72,
      "status": "learning"
    }
  ],
  "edges": [
    {
      "source": "programming",
      "target": "data-structures"
    }
  ]
}
```

---

# 20. DAG interaction

Three.js graph should support:

- rotate
- zoom
- pan
- hover
- click node
- focus node
- reset/recenter

Node visual state should reflect mastery.

Clicking a node should show something like:

```text
Algorithms

Mastery: 68%
Status: Learning

Prerequisites:
Data Structures

Next:
Graph Algorithms
Dynamic Programming
```

Do not make the 3D scene decorative only.

It must represent real learning data.

Provide a usable 2D/fallback experience if WebGL is unavailable.

---

# 21. Roadmap

Create:

```text
/roadmap
```

Reuse DAG data.

Clearly show:

```text
Completed
Current
Next
Locked
```

Highlight the adaptive system's recommended next skill.

---

# 22. History

Create:

```text
/history
```

Show:

```text
Activity
Skill
Type
Score
Date
Status
```

Activity details should show:

- activity
- learner answer
- evaluation
- score
- feedback
- mastery change when available

Use existing activity/evidence/attempt data.

---

# 23. Profile/settings

Create:

```text
/profile
/settings
```

Show:

```text
name
email
learning interests
learning goals
current level
```

Possible preferences:

```text
theme
notifications
learning preferences
```

Do not expose internal implementation details such as raw database IDs or theta unless deliberately designed as an educational metric.

---

# 24. Dashboard

Final dashboard should look approximately like:

```text
Welcome back, <name>

Continue Learning
┌────────────────────────────────────┐
│ Current skill                      │
│ Programming Fundamentals           │
│ Mastery 72%                        │
│                                    │
│ Current activity                   │
│ Fixing Logic Errors                │
│                         Continue → │
└────────────────────────────────────┘

Progress
┌────────┐ ┌────────┐ ┌─────────────┐
│ 72%    │ │ 18     │ │ 7           │
│ Mastery│ │ Skills │ │ Activities  │
└────────┘ └────────┘ └─────────────┘

Learning Path
[small DAG preview]

Recent Activity
...
```

---

# 25. Dark-purple design system

Use a premium dark-purple aesthetic.

Visual direction:

```text
Background:
near-black / very dark purple

Cards:
dark violet

Primary:
electric purple

Secondary:
soft lavender

Text:
white / light lavender

Muted text:
cool gray-purple

Borders:
subtle translucent purple

Success:
restrained green

Warning:
restrained amber
```

Use:

- clean typography
- rounded corners
- subtle gradients
- subtle shadows
- restrained glass effects
- consistent spacing
- smooth but minimal animations

Avoid an overly neon/gaming appearance.

---

# 26. Navigation

Recommended:

```text
LearnAI
────────────
Dashboard
Learn
Roadmap
Progress
History
────────────
Profile
Settings
────────────
Logout
```

Responsive behavior:

- desktop sidebar
- mobile drawer or bottom navigation

---

# 27. Environment configuration

Do not hardcode the frontend API URL.

Use:

```text
VITE_API_BASE_URL
```

Example:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Backend secrets should use environment variables:

```text
DATABASE_URL
JWT_SECRET
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
GEMINI_API_KEY
```

Never commit secrets.

---

# 28. Authentication security

Must:

- hash passwords securely
- never log passwords
- never expose password hashes
- protect JWT secret
- authorize learner ownership
- protect learner APIs
- prevent cross-user data access

Do not trust:

```text
/api/learners/{arbitrary_id}
```

without verifying ownership.

---

# 29. AI responsibility boundaries

Application code should control:

```text
authentication
authorization
database persistence
assessment scoring
mastery calculations
recommendation state
conversation state
graph structure
```

Gemini should assist with:

```text
tutoring
explanations
hints
natural-language interpretation
activity generation
appropriate open-ended evaluation
conversational onboarding
```

Do not make Gemini the source of truth for deterministic business logic.

---

# 30. Error handling

Every page needs:

### Loading

Use skeletons or polished loaders.

### Error

Show a useful message and retry action.

### Empty

Example:

```text
No learning history yet.

Complete your first activity to start
building your learning history.
```

### Gemini failure

Never show:

```text
RESOURCE_EXHAUSTED
```

or provider stack traces directly to the learner.

Instead:

```text
LearnAI is temporarily unavailable.
Your progress is safe. Please try again.
```

---

# 31. Development discipline

Before modifying a file:

1. Inspect the existing implementation.
2. Understand imports/dependencies.
3. Preserve working behavior.
4. Make a coherent minimal change.
5. Run the relevant build/test.
6. Fix errors immediately.
7. Move to the next feature only after the current feature works.

Do not:

- rewrite the whole project
- create duplicate services
- create a second learner model
- create a second adaptive loop
- hardcode production learner IDs
- add unnecessary dependencies
- replace working APIs for stylistic reasons

---

# 32. Suggested implementation order

## Phase A — Authentication

Build:

```text
User model
Learner relationship
Password hashing
JWT
Signup
Login
Me
Protected APIs
```

Verify with Swagger.

## Phase B — Authenticated learning

Replace the hardcoded learner ID with:

```text
JWT
 ↓
User
 ↓
Learner
```

Verify the adaptive loop still works.

## Phase C — Conversational onboarding

Implement:

```text
Goal
Interests
Background
Five-question assessment
Initial learner state
```

## Phase D — Persistent chat

Implement:

```text
ChatSession
ChatMessage
```

## Phase E — Analytics

Build:

```text
Progress
Charts
Statistics
```

## Phase F — DAG / roadmap

Build:

```text
Skill graph
Three.js visualization
Roadmap
```

## Phase G — History/profile

Build:

```text
History
Profile
Settings
```

## Phase H — UI polish

Apply the final dark-purple system across all pages.

## Phase I — Full integration testing

Test:

```text
New user
 ↓
Signup
 ↓
Login
 ↓
Onboarding conversation
 ↓
Five questions
 ↓
Learner model
 ↓
Dashboard
 ↓
Roadmap
 ↓
Recommended activity
 ↓
Tutor chat
 ↓
Submit
 ↓
Evaluation
 ↓
Evidence
 ↓
Mastery update
 ↓
New recommendation
 ↓
Progress chart
```

Only then deploy.

---

# 33. Master instruction for Antigravity

You are completing an existing project named **LearnAI**, an AI-powered adaptive learning platform.

Do not start from scratch.

First inspect the entire repository and understand the current architecture.

The project already contains:

- FastAPI backend
- SQLAlchemy database
- learner model
- learner skill states
- evidence system
- adaptive recommendation loop
- activity generation
- activity evaluation
- Gemini/LangChain integration
- conversational tutor
- React + TypeScript + Vite frontend
- dashboard
- Learn page
- API client

Preserve working functionality.

Your mission is to complete the product.

Implement the remaining features in this order:

1. User authentication
2. User → Learner relationship
3. JWT authentication
4. Signup/login
5. Authenticated learner resolution
6. New-user conversational onboarding
7. Goal/interest/background collection
8. Five-question initial assessment
9. Initial learner state/evidence
10. Persistent conversations
11. Progress analytics
12. Real-data charts
13. Skill dependency DAG
14. Three.js interactive graph
15. Learning roadmap
16. Activity history
17. Profile/settings
18. Final dark-purple UI
19. Responsive/mobile polish
20. Loading/error/empty states
21. Full integration testing

Preserve the existing adaptive loop.

Do not create duplicate business logic.

Do not hardcode learner IDs in production.

Do not trust frontend learner IDs for authorization.

Do not store plaintext passwords.

Do not expose secrets.

Do not expose raw Gemini errors.

Do not make Gemini responsible for deterministic application logic.

For the tutor:

- use learner context
- use current activity
- use mastery/confidence
- use evidence
- use conversation history
- treat activity requirements as authoritative
- teach instead of always revealing answers
- provide hints
- adapt to ability
- handle Gemini failures gracefully

For `/next-activity`:

- reuse suitable existing activities
- avoid unnecessary Gemini calls
- generate only when necessary
- gracefully handle LLM failures

For onboarding:

```text
NEW
→ DISCOVERING_GOAL
→ DISCOVERING_INTERESTS
→ DISCOVERING_BACKGROUND
→ ASSESSMENT
→ PROFILE_READY
→ LEARNING
```

The backend owns this state.

For the initial assessment:

- approximately five questions
- domain-specific
- measurable
- objective evidence
- feed results into the existing learner model

For analytics:

- use real data
- never fabricate values

For the DAG:

- use actual skill dependencies
- show mastery/status
- support zoom/pan/hover/click/focus
- use Three.js / React Three Fiber
- provide fallback behavior

For UI:

Create a premium dark-purple education product.

The design should be:

- modern
- clean
- intelligent
- minimal
- readable
- responsive
- subtle
- not excessively neon
- not excessively gamified

After each major implementation:

```text
run backend checks
run frontend TypeScript/build
fix errors
verify routes
verify migrations
verify API behavior
```

Do not leave broken code behind.

At completion report:

1. Changes made
2. New files
3. Modified files
4. Database migrations/tables
5. API endpoints
6. Frontend routes
7. Dependencies
8. Environment variables
9. Run commands
10. End-to-end test instructions
11. Remaining limitations

The priority is:

**complete working product > fancy implementation > unnecessary complexity.**

---

# 34. Definition of done

A new person should be able to:

```text
Create account
 ↓
Log in
 ↓
Talk to LearnAI
 ↓
Explain what they want to learn
 ↓
Answer five assessment questions
 ↓
Receive personalized starting point
 ↓
See dashboard
 ↓
See learning roadmap/DAG
 ↓
Receive recommended activity
 ↓
Ask tutor questions
 ↓
Submit solution
 ↓
Receive evaluation
 ↓
Learner model updates
 ↓
Progress changes
 ↓
New activity is recommended
 ↓
Return later
 ↓
Progress and conversation remain available
```

The defining feature is not the chatbot, charts, or 3D graph individually.

The defining feature is:

```text
Learner
   ↓
Evidence
   ↓
Learner Model
   ↓
Adaptive Recommendation
   ↓
Activity
   ↓
Feedback
   ↓
Updated Learner Model
   ↓
Better Next Recommendation
```

Everything else should make that adaptive loop understandable, usable, and visually compelling.
