import { useEffect, useMemo, useState, type ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";

import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Onboarding from "./pages/Onboarding";
import Learn from "./pages/Learn";
import Progress from "./pages/Progress";
import Roadmap from "./pages/Roadmap";
import History from "./pages/History";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";

import {
  getActivityHistory,
  getLearnerState,
  getNextActivity,
} from "./services/api";

import type {
  ActivityHistoryResponse,
  LearnerStateResponse,
  NextActivityResponse,
} from "./types/learning";

import "./App.css";

import {
  BarChart3,
  BookOpen,
  Loader2,
  Map,
  RefreshCw,
} from "lucide-react";

// ─── Route guards ─────────────────────────────────────────────────────────────

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="full-page-loader">
        <Loader2 className="spin" size={36} />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  return <>{children}</>;
}

function OnboardingGuard({ children }: { children: ReactNode }) {
  const { user } = useAuth();

  // If user exists but onboarding not done, redirect to onboarding
  if (user && user.onboarding_state !== "LEARNING") {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

function Dashboard() {
  const { user, learnerId } = useAuth();
  const navigate = useNavigate();

  const [learnerState, setLearnerState] = useState<LearnerStateResponse | null>(null);
  const [nextActivity, setNextActivity] = useState<NextActivityResponse | null>(null);
  const [activityHistory, setActivityHistory] = useState<ActivityHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard() {
    if (!learnerId) return;
    try {
      setLoading(true);
      setError(null);
      const [state, activity, history] = await Promise.all([
        getLearnerState(learnerId),
        getNextActivity(learnerId).catch(() => null),
        getActivityHistory(learnerId),
      ]);
      setLearnerState(state);
      setNextActivity(activity);
      setActivityHistory(history);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadDashboard(); }, [learnerId]);

  const overallMastery = useMemo(() => {
    if (!learnerState || learnerState.skills.length === 0) return 0;
    const total = learnerState.skills.reduce((sum, s) => sum + s.mastery, 0);
    return Math.round((total / learnerState.skills.length) * 100);
  }, [learnerState]);

  if (loading) return (
    <div className="page-loading">
      <Loader2 className="spin" size={32} />
      <p>Loading your dashboard...</p>
    </div>
  );

  if (error) return (
    <div className="page-error">
      <p>{error}</p>
      <button className="primary-button" onClick={loadDashboard}>
        <RefreshCw size={16} /> Retry
      </button>
    </div>
  );

  const displayName = user?.display_name ?? user?.username ?? "Learner";

  return (
    <div className="page-content">
      {/* Welcome */}
      <div className="welcome">
        <div>
          <p className="welcome-label">Welcome back</p>
          <h1>Hello, {displayName} 👋</h1>
          <p>Your learning path adapts to your performance and progress.</p>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <p className="stat-label">Overall mastery</p>
          <p className="stat-value">{overallMastery}%</p>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${overallMastery}%` }} />
          </div>
          <p className="stat-description">Across your tracked skills</p>
        </div>

        <div className="stat-card">
          <p className="stat-label">Current skill</p>
          <p className="stat-value stat-value-text">
            {nextActivity?.skill.label ?? "—"}
          </p>
          <p className="stat-description">Currently learning</p>
        </div>

        <div className="stat-card">
          <p className="stat-label">Activities completed</p>
          <p className="stat-value">{activityHistory?.activities_completed ?? 0}</p>
          <p className="stat-description">Keep going!</p>
        </div>
      </div>

      {/* Quick nav */}
      <div className="quick-nav">
        <button className="quick-nav-card" onClick={() => navigate("/learn")}>
          <BookOpen size={22} />
          <span>Continue learning</span>
        </button>
        <button className="quick-nav-card" onClick={() => navigate("/roadmap")}>
          <Map size={22} />
          <span>View roadmap</span>
        </button>
        <button className="quick-nav-card" onClick={() => navigate("/progress")}>
          <BarChart3 size={22} />
          <span>See progress</span>
        </button>
      </div>

      {/* Recommended activity */}
      {nextActivity && (
        <section className="section">
          <div className="section-header">
            <div>
              <p className="section-eyebrow">Recommended</p>
              <h2>Continue learning</h2>
            </div>
            <button className="text-button" onClick={() => navigate("/history")}>View all</button>
          </div>

          <div className="learning-card">
            <div className="learning-card-content">
              <div className="skill-badge">{nextActivity.skill.label}</div>
              <h3>{nextActivity.activity.title}</h3>
              <p>{nextActivity.activity.objective}</p>

              <div className="progress-section">
                <div className="progress-header">
                  <span>Current mastery</span>
                  <span>
                    {Math.round(
                      (learnerState?.skills.find((s) => s.skill_id === nextActivity.skill.id)?.mastery ?? 0) * 100,
                    )}%
                  </span>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${
                        (learnerState?.skills.find((s) => s.skill_id === nextActivity.skill.id)?.mastery ?? 0) * 100
                      }%`,
                    }}
                  />
                </div>
              </div>

              <button className="primary-button" onClick={() => navigate("/learn")}>
                Continue learning
              </button>
            </div>

            <div className="learning-card-side">
              <span className="activity-type">{nextActivity.activity.type}</span>
              <span className="difficulty">{nextActivity.activity.difficulty}</span>
            </div>
          </div>
        </section>
      )}

      {/* Recent activities */}
      {activityHistory && activityHistory.activities.length > 0 && (
        <section className="section">
          <div className="section-header">
            <div>
              <p className="section-eyebrow">Recent</p>
              <h2>Activity history</h2>
            </div>
            <button className="text-button" onClick={() => navigate("/history")}>View all</button>
          </div>

          <div className="recent-list">
            {activityHistory.activities.slice(0, 4).map((a) => (
              <div key={a.activity_id} className="recent-item">
                <div>
                  <p className="recent-title">{a.title}</p>
                  <p className="recent-meta">{a.skill_id} · {a.type}</p>
                </div>
                <span className="difficulty">{a.difficulty}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Semi-protected: requires auth but not LEARNING state */}
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />

      {/* Protected + onboarding complete */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <OnboardingGuard>
              <Layout><Dashboard /></Layout>
            </OnboardingGuard>
          </ProtectedRoute>
        }
      />
      <Route
        path="/learn"
        element={
          <ProtectedRoute>
            <OnboardingGuard>
              <Layout>
                <Learn onBack={() => window.history.back()} />
              </Layout>
            </OnboardingGuard>
          </ProtectedRoute>
        }
      />
      <Route
        path="/roadmap"
        element={
          <ProtectedRoute>
            <OnboardingGuard>
              <Layout><Roadmap /></Layout>
            </OnboardingGuard>
          </ProtectedRoute>
        }
      />
      <Route
        path="/progress"
        element={
          <ProtectedRoute>
            <OnboardingGuard>
              <Layout><Progress /></Layout>
            </OnboardingGuard>
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <OnboardingGuard>
              <Layout><History /></Layout>
            </OnboardingGuard>
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <OnboardingGuard>
              <Layout><Profile /></Layout>
            </OnboardingGuard>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <OnboardingGuard>
              <Layout><Settings /></Layout>
            </OnboardingGuard>
          </ProtectedRoute>
        }
      />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
