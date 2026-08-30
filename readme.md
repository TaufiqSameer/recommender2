# LearnAI

## AI-Powered Adaptive Learning Platform

LearnAI is an AI-powered adaptive learning platform that creates a personalized learning experience for each learner.

The system combines a learner model, adaptive recommendations, learning activities, AI evaluation, and a conversational AI tutor.

---

## How the Project Works

The main learning loop is:

```text
Learner
   ↓
Learning Activity
   ↓
Learner Attempts Activity
   ↓
AI Evaluation
   ↓
Learning Evidence
   ↓
Learner Model Updated
   ↓
Adaptive Recommendation
   ↓
Next Activity
```

The learner model tracks information such as mastery, confidence, attempts, skill status, and learning evidence.

The adaptive system uses this information to determine what the learner should learn next.

The LearnAI chatbot acts as a personal learning tutor. It uses the learner's current skill, mastery, confidence, activity, recent evidence, and conversation history to provide personalized explanations and guidance.

---

## Technologies Used

### Frontend
- React
- TypeScript
- Vite
- React Router
- Lucide React
- Three.js / React Three Fiber
- Charting libraries

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- LangChain

### Database
- PostgreSQL

### AI
- Google Gemini
- LangChain

### Authentication
- JWT
- Secure password hashing

---

## Main Features

### Adaptive Learning

LearnAI continuously updates the learner's skill state based on their performance.

```text
Initial Mastery
      ↓
Learner completes activity
      ↓
Activity is evaluated
      ↓
Evidence is recorded
      ↓
Mastery is updated
      ↓
Next activity is selected
```

### AI Tutor

The LearnAI chatbot provides a conversational learning experience. It can explain concepts, answer learning questions, provide hints, help debug solutions, explain mistakes, provide feedback, and adapt explanations to learner ability.

### Learning Activities

Activities can include coding exercises, debugging tasks, conceptual questions, and other learning exercises.

Each activity contains information such as skill, objective, difficulty, instructions, hints, and activity type.

### AI Evaluation

Learner submissions are evaluated and converted into learning evidence. Evaluation can provide a score, correctness, feedback, strengths, weaknesses, and a suggested next step.

### Progress Analytics

The application provides visual information about learner progress, including overall mastery, skill mastery, activity performance, mastery trends, and learning history.

### Skill Learning Graph

Skills can be represented as a dependency graph.

```text
Programming Fundamentals
          ↓
     Control Flow
          ↓
       Functions
          ↓
    Data Structures
          ↓
       Algorithms
```

The graph represents prerequisite relationships between skills and can be visualized using Three.js.

---

# Running the Project

## Requirements

Install:

- Python 3.11 or newer
- Node.js
- npm
- PostgreSQL
- Gemini API key

Verify the installations:

```bash
python --version
node --version
npm --version
```

---

# 1. Backend Setup

Open a terminal in the project directory:

```bash
cd backend
```

Create a Python virtual environment.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The virtual environment keeps the project's Python dependencies isolated from the system Python installation.

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

---

# 2. Configure Environment Variables

Create a `.env` file inside the backend directory.

Example:

```env
DATABASE_URL=your_postgresql_database_url
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET=your_secret_key
```

Use the actual PostgreSQL connection string and Gemini API key for the environment.

Do not commit the real `.env` file or API keys to the repository.

---

# 3. PostgreSQL Database

Make sure PostgreSQL is running.

Create the database specified by `DATABASE_URL`.

For example:

```sql
CREATE DATABASE learnai;
```

The database stores users, learners, skills, learner skill states, learning evidence, learning activities, assessment attempts, assessment answers, chat sessions, and chat messages.

If the project uses Alembic migrations, run:

```bash
alembic upgrade head
```

This applies the database schema and creates the required tables.

---

# 4. Start the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The backend normally runs at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Keep this terminal running.

---

# 5. Frontend Setup

Open a second terminal.

Navigate to the frontend:

```bash
cd frontend
```

Install the frontend dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend normally runs at:

```text
http://localhost:5173
```

Open this address in a browser.

---

# 6. Running the Application

Both the backend and frontend must be running.

The application architecture is:

```text
Browser
   ↓
React Frontend
   ↓
FastAPI Backend
   ↓
PostgreSQL
   ↓
Gemini AI
```

The typical learner flow is:

```text
Create Account
      ↓
Login
      ↓
Tell LearnAI what you want to learn
      ↓
Initial Assessment
      ↓
Learner Model Created
      ↓
Personalized Activity Recommended
      ↓
Interact with LearnAI Tutor
      ↓
Submit Activity
      ↓
AI Evaluation
      ↓
Learning Evidence Recorded
      ↓
Learner Mastery Updated
      ↓
Next Activity Recommended
```

---

# 7. Adaptive Learning Example

Suppose a learner starts with:

```text
Programming Fundamentals
Mastery: 39%
```

The learner completes an activity successfully.

The system records the result as learning evidence.

The learner model is then updated:

```text
39% → 57%
```

The adaptive engine uses the new learner state to determine an appropriate next activity.

This creates a continuous learning loop:

```text
Activity
   ↓
Attempt
   ↓
Evaluation
   ↓
Evidence
   ↓
Mastery Update
   ↓
Recommendation
   ↓
Next Activity
```

---

# 8. AI Tutor

The LearnAI chatbot receives relevant learner context, including:

- Current skill
- Current mastery
- Current confidence
- Current activity
- Recent learning evidence
- Conversation history

The tutor is designed to teach rather than simply provide answers.

For example:

```text
Learner asks a question
        ↓
Tutor explains concept
        ↓
Tutor provides hint
        ↓
Learner attempts solution
        ↓
Tutor reviews attempt
        ↓
Tutor explains mistakes
```

The current activity instructions are treated as authoritative so that the tutor remains consistent with the exercise.

---

# 9. Authentication

LearnAI uses authenticated users rather than relying on a hardcoded learner ID.

The authentication flow is:

```text
Signup
   ↓
Create User
   ↓
Create Learner Profile
   ↓
Authenticate
   ↓
Dashboard
```

Login:

```text
Email + Password
       ↓
Verify Password
       ↓
JWT Access Token
       ↓
Authenticated Requests
```

Typical endpoints include:

```text
POST /api/auth/signup
POST /api/auth/login
GET  /api/auth/me
```

Passwords are stored as secure password hashes rather than plaintext passwords.

---

# 10. Project Structure

```text
LearnAI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── ai/
│   │   ├── db/
│   │   └── services/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── ...
│
└── README.md
```

The backend contains API routes, database models, the adaptive learning engine, learner services, AI services, and authentication.

The frontend contains the dashboard, learning interface, AI chatbot, progress visualization, learning roadmap, and authentication pages.

---

# 11. Verify the Frontend Build

Before submitting the project, verify that the frontend builds successfully.

From the frontend directory:

```bash
npm run build
```

The command should complete without TypeScript or Vite errors.

---

# Quick Start

After the initial setup, two terminals are required.

## Terminal 1 — Backend

```bash
cd backend
```

Windows:

```bash
.venv\Scripts\activate
```

Then:

```bash
uvicorn app.main:app --reload
```

## Terminal 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:5173
```

---

# Important Notes

- PostgreSQL must be running before starting the backend.
- The backend `.env` file must contain valid configuration.
- The backend must be running before using the frontend.
- Gemini API usage is subject to API quotas and rate limits.
- Never commit API keys or database passwords.
- The application should gracefully handle temporary AI-provider failures.
