import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getOnboardingStatus } from "../services/api";
import {
  Loader2,
  User,
  Mail,
  Target,
  BookOpen,
  Layers,
  Clock,
  Briefcase,
  Sliders,
} from "lucide-react";

export default function Profile() {
  const { user, learnerId } = useAuth();
  const navigate = useNavigate();
  const [domain, setDomain] = useState<string | null>(null);
  const [goal, setGoal] = useState<string | null>(null);
  const [onboardingState, setOnboardingState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOnboardingStatus()
      .then((s) => {
        setDomain(s.domain);
        setGoal(s.goal);
        setOnboardingState(s.state);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="page-loading">
        <Loader2 className="spin" size={32} />
      </div>
    );

  const displayName = user?.display_name ?? user?.username ?? "Learner";
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <p className="eyebrow">Your Account & Tracked Skills</p>
          <h1>Profile</h1>
        </div>
        <button
          className="secondary-button"
          onClick={() => navigate("/settings")}
        >
          <Sliders size={16} />
          <span>Edit in Settings</span>
        </button>
      </div>

      <div className="profile-grid">
        {/* Avatar + hero card */}
        <div className="profile-card profile-hero">
          <div className="profile-avatar-lg">{initial}</div>
          <h2 className="profile-name">{displayName}</h2>
          <p className="profile-username">@{user?.username}</p>
          {onboardingState && (
            <span
              className={`status-badge ${
                onboardingState === "LEARNING" ? "active" : ""
              }`}
            >
              {onboardingState === "LEARNING"
                ? "Active Learner"
                : onboardingState.replace(/_/g, " ")}
            </span>
          )}

          <div className="profile-hero-stats">
            <div className="hero-stat">
              <span className="stat-num">{user?.weekly_hours ?? 5}h</span>
              <span className="stat-lbl">Weekly Target</span>
            </div>
            <div className="hero-stat">
              <span className="stat-num">{domain ?? "Backend"}</span>
              <span className="stat-lbl">Primary Track</span>
            </div>
          </div>
        </div>

        {/* Account Details */}
        <div className="profile-card">
          <h3>Account Details</h3>

          <div className="profile-field">
            <User size={16} />
            <div>
              <p className="field-label">Username</p>
              <p>{user?.username}</p>
            </div>
          </div>

          <div className="profile-field">
            <Mail size={16} />
            <div>
              <p className="field-label">Email Address</p>
              <p>{user?.email}</p>
            </div>
          </div>

          <div className="profile-field">
            <Layers size={16} />
            <div>
              <p className="field-label">Learner Profile ID</p>
              <p className="mono">{learnerId}</p>
            </div>
          </div>
        </div>

        {/* Learning Profile */}
        <div className="profile-card">
          <h3>Learning Track & Goals</h3>

          <div className="profile-field">
            <Briefcase size={16} />
            <div>
              <p className="field-label">Target Role</p>
              <p>{user?.target_role ?? "Backend Engineer"}</p>
            </div>
          </div>

          <div className="profile-field">
            <BookOpen size={16} />
            <div>
              <p className="field-label">Domain Track</p>
              <p>{domain ?? user?.domain ?? "Backend Development"}</p>
            </div>
          </div>

          <div className="profile-field">
            <Target size={16} />
            <div>
              <p className="field-label">Primary Goal</p>
              <p>{goal || user?.goal || "Master core concepts and advance to professional level"}</p>
            </div>
          </div>

          <div className="profile-field">
            <Clock size={16} />
            <div>
              <p className="field-label">Weekly Study Target</p>
              <p>{user?.weekly_hours ?? 5} hours per week</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
