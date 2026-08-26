import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  BarChart3,
  BookOpen,
  Clock3,
  LayoutDashboard,
  Settings,
  UserCircle,
} from "lucide-react";

import "./App.css";

import {
  getActivityHistory,
  getLearnerState,
  getNextActivity,
} from "./services/api";

import type {
  ActivityHistoryItem,
  LearnerStateResponse,
  NextActivityResponse,
} from "./types/learning";

import {
  CURRENT_LEARNER_ID,
} from "./config/learner";


function App() {

  const [
    learnerState,
    setLearnerState,
  ] = useState<LearnerStateResponse | null>(
    null,
  );


  const [
    nextActivity,
    setNextActivity,
  ] = useState<NextActivityResponse | null>(
    null,
  );


  const [
    activities,
    setActivities,
  ] = useState<ActivityHistoryItem[]>(
    [],
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  useEffect(() => {

    async function loadDashboard() {

      try {

        setLoading(true);

        setError(null);


        const [
          state,
          activity,
          history,
        ] = await Promise.all([
          getLearnerState(
            CURRENT_LEARNER_ID,
          ),

          getNextActivity(
            CURRENT_LEARNER_ID,
          ),

          getActivityHistory(
            CURRENT_LEARNER_ID,
          ),
        ]);


        setLearnerState(state);

        setNextActivity(activity);

        setActivities(history);

      } catch (err) {

        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(
            "Failed to load dashboard.",
          );
        }

      } finally {

        setLoading(false);

      }
    }


    loadDashboard();

  }, []);


  const overallMastery = useMemo(() => {

    if (
      !learnerState ||
      learnerState.skills.length === 0
    ) {
      return 0;
    }


    const total = learnerState.skills.reduce(
      (sum, skill) =>
        sum + skill.mastery,
      0,
    );


    return Math.round(
      (total /
        learnerState.skills.length) *
        100,
    );

  }, [learnerState]);


  if (loading) {

    return (
      <div className="app-shell">

        <main className="main-content">

          <div className="dashboard">

            <div className="welcome">

              <p className="welcome-label">
                Adaptive Learning
              </p>

              <h2>
                Loading your learning path...
              </h2>

            </div>

          </div>

        </main>

      </div>
    );
  }


  if (error) {

    return (
      <div className="app-shell">

        <main className="main-content">

          <div className="dashboard">

            <div className="welcome">

              <p className="welcome-label">
                Connection Error
              </p>

              <h2>
                Unable to load your dashboard.
              </h2>

              <p>
                {error}
              </p>

            </div>

          </div>

        </main>

      </div>
    );
  }


  return (
    <div className="app-shell">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">
            L
          </div>

          <span className="brand-name">
            LearnAI
          </span>

        </div>


        <nav className="sidebar-nav">

          <a
            href="#"
            className="nav-item active"
          >
            <LayoutDashboard size={19} />
            <span>
              Dashboard
            </span>
          </a>


          <a
            href="#"
            className="nav-item"
          >
            <BookOpen size={19} />
            <span>
              Learn
            </span>
          </a>


          <a
            href="#"
            className="nav-item"
          >
            <BarChart3 size={19} />
            <span>
              Progress
            </span>
          </a>


          <a
            href="#"
            className="nav-item"
          >
            <Clock3 size={19} />
            <span>
              History
            </span>
          </a>

        </nav>


        <div className="sidebar-bottom">

          <a
            href="#"
            className="nav-item"
          >
            <Settings size={19} />
            <span>
              Settings
            </span>
          </a>


          <a
            href="#"
            className="nav-item"
          >
            <UserCircle size={19} />
            <span>
              Profile
            </span>
          </a>

        </div>

      </aside>


      <main className="main-content">

        <header className="topbar">

          <div>

            <p className="eyebrow">
              Adaptive Learning
            </p>

            <h1>
              Your learning dashboard
            </h1>

          </div>


          <div className="profile">

            <div className="profile-avatar">
              S
            </div>

            <div>

              <p className="profile-name">
                Learner
              </p>

              <p className="profile-role">
                Student
              </p>

            </div>

          </div>

        </header>


        <section className="dashboard">

          <div className="welcome">

            <div>

              <p className="welcome-label">
                Continue your journey
              </p>

              <h2>
                Keep building your skills.
              </h2>

              <p>
                Your learning path adapts to
                your performance and progress.
              </p>

            </div>

          </div>


          <div className="stats-grid">

            <div className="stat-card">

              <p className="stat-label">
                Overall mastery
              </p>

              <p className="stat-value">
                {overallMastery}%
              </p>

              <p className="stat-description">
                Across your tracked skills
              </p>

            </div>


            <div className="stat-card">

              <p className="stat-label">
                Current skill
              </p>

              <p className="stat-value stat-value-text">

                {nextActivity?.skill.label ??
                  "No active skill"}

              </p>

              <p className="stat-description">
                Currently learning
              </p>

            </div>


            <div className="stat-card">

              <p className="stat-label">
                Activities completed
              </p>

              <p className="stat-value">
                {activities.length}
              </p>

              <p className="stat-description">
                Keep going
              </p>

            </div>

          </div>


          <section className="section">

            <div className="section-header">

              <div>

                <p className="section-eyebrow">
                  Recommended
                </p>

                <h2>
                  Continue learning
                </h2>

              </div>

              <button className="text-button">
                View all
              </button>

            </div>


            {nextActivity && (

              <div className="learning-card">

                <div className="learning-card-content">

                  <div className="skill-badge">

                    {nextActivity.skill.label}

                  </div>


                  <h3>

                    {nextActivity.activity.title}

                  </h3>


                  <p>

                    {nextActivity.activity.objective}

                  </p>


                  <div className="progress-section">

                    <div className="progress-header">

                      <span>
                        Current mastery
                      </span>

                      <span>
                        {Math.round(
                          (
                            learnerState?.skills.find(
                              skill =>
                                skill.skill_id ===
                                nextActivity.skill.id,
                            )?.mastery ?? 0
                          ) * 100,
                        )}
                        %
                      </span>

                    </div>


                    <div className="progress-track">

                      <div
                        className="progress-fill"
                        style={{
                          width: `${
                            (
                              learnerState?.skills.find(
                                skill =>
                                  skill.skill_id ===
                                  nextActivity.skill.id,
                              )?.mastery ?? 0
                            ) * 100
                          }%`,
                        }}
                      />

                    </div>

                  </div>


                  <button className="primary-button">
                    Continue learning
                  </button>

                </div>


                <div className="learning-card-side">

                  <span className="activity-type">

                    {nextActivity.activity.type}

                  </span>


                  <span className="difficulty">

                    {nextActivity.activity.difficulty}

                  </span>

                </div>

              </div>

            )}

          </section>

        </section>

      </main>

    </div>
  );
}


export default App;