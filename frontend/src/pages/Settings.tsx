import { useState, useEffect, type FormEvent } from "react";
import { useAuth } from "../context/AuthContext";
import { updateMe } from "../services/api";
import {
  Loader2,
  Save,
  CheckCircle,
  Sliders,
  User,
  Clock,
  Sparkles,
  BookOpen,
} from "lucide-react";

const LEARNING_STYLES = [
  { id: "projects", label: "Project-based", desc: "Build realistic, portfolio-ready systems" },
  { id: "exercises", label: "Hands-on exercises", desc: "Short focused coding & architecture drills" },
  { id: "theory", label: "Concepts & Theory", desc: "Deep conceptual and mathematical foundations" },
  { id: "step_by_step", label: "Step-by-step challenges", desc: "Guided incremental skill progression" },
];

export default function Settings() {
  const { user, refreshUser } = useAuth();

  const [displayName, setDisplayName] = useState(user?.display_name ?? user?.username ?? "");
  const [goal, setGoal] = useState(user?.goal ?? "");
  const [targetRole, setTargetRole] = useState(user?.target_role ?? "Backend Engineer");
  const [weeklyHours, setWeeklyHours] = useState<number>(user?.weekly_hours ?? 5);
  const [selectedStyles, setSelectedStyles] = useState<string[]>(
    Array.isArray(user?.learning_preferences) ? user.learning_preferences : ["exercises", "projects"]
  );
  const [animationsEnabled, setAnimationsEnabled] = useState(true);

  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name ?? user.username ?? "");
      setGoal(user.goal ?? "");
      setTargetRole(user.target_role ?? "Backend Engineer");
      setWeeklyHours(user.weekly_hours ?? 5);
      if (Array.isArray(user.learning_preferences) && user.learning_preferences.length > 0) {
        setSelectedStyles(user.learning_preferences);
      }
    }
  }, [user]);

  function toggleStyle(id: string) {
    setSelectedStyles((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSavedSuccess(false);

    try {
      await updateMe({
        display_name: displayName,
        goal: goal,
        target_role: targetRole,
        weekly_hours: weeklyHours,
        learning_preferences: selectedStyles,
        preferences: {
          animations: animationsEnabled,
        },
      });

      await refreshUser();
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <p className="eyebrow">Personalization & Account</p>
          <h1>Settings</h1>
        </div>
      </div>

      {savedSuccess && (
        <div className="settings-alert-success">
          <CheckCircle size={18} color="#22c55e" />
          <span>Your settings have been saved successfully!</span>
        </div>
      )}

      {error && (
        <div className="auth-error" style={{ marginBottom: "1.5rem" }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSave} className="settings-form">
        {/* Profile Details Section */}
        <section className="settings-section">
          <div className="settings-section-header">
            <User size={20} className="section-icon" />
            <div>
              <h2>Profile Details</h2>
              <p>Customize how you appear in LearnAI</p>
            </div>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="settings-name">Display Name</label>
              <input
                id="settings-name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your preferred name"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="settings-role">Target Role</label>
              <input
                id="settings-role"
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g. Backend Engineer, Systems Architect"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: "1rem" }}>
            <label htmlFor="settings-goal">Learning Goal</label>
            <textarea
              id="settings-goal"
              rows={3}
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="What are you hoping to build or achieve with LearnAI?"
            />
          </div>
        </section>

        {/* Adaptive Learning Preferences */}
        <section className="settings-section">
          <div className="settings-section-header">
            <Sliders size={20} className="section-icon" />
            <div>
              <h2>Learning Preferences</h2>
              <p>Configure how LearnAI tailors your exercises and pace</p>
            </div>
          </div>

          <div className="form-group">
            <label className="section-sublabel">
              <Clock size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              Weekly Commitment ({weeklyHours} hours / week)
            </label>
            <div className="range-slider-row">
              <input
                type="range"
                min={1}
                max={30}
                step={1}
                value={weeklyHours}
                onChange={(e) => setWeeklyHours(Number(e.target.value))}
                className="range-input"
              />
              <span className="range-val-badge">{weeklyHours} hrs</span>
            </div>
            <p className="field-hint">
              LearnAI adjusts recommendation velocity based on your scheduled time.
            </p>
          </div>

          <div className="form-group" style={{ marginTop: "1.5rem" }}>
            <label className="section-sublabel">
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              Preferred Learning Styles
            </label>
            <div className="styles-grid">
              {LEARNING_STYLES.map((st) => {
                const active = selectedStyles.includes(st.id);
                return (
                  <div
                    key={st.id}
                    className={`style-card ${active ? "active" : ""}`}
                    onClick={() => toggleStyle(st.id)}
                  >
                    <div className="style-card-header">
                      <strong>{st.label}</strong>
                      <div className={`checkbox-custom ${active ? "checked" : ""}`} />
                    </div>
                    <p>{st.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Interface Preferences */}
        <section className="settings-section">
          <div className="settings-section-header">
            <Sparkles size={20} className="section-icon" />
            <div>
              <h2>Interface & Theme</h2>
              <p>Dark-purple aesthetic and visual animation options</p>
            </div>
          </div>

          <div className="settings-toggle-row">
            <div>
              <strong>Smooth 3D & UI Animations</strong>
              <p className="field-hint">Enable glowing halos, floating badges, and smooth graph transitions</p>
            </div>
            <label className="switch">
              <input
                type="checkbox"
                checked={animationsEnabled}
                onChange={(e) => setAnimationsEnabled(e.target.checked)}
              />
              <span className="slider round" />
            </label>
          </div>
        </section>

        {/* Submit action */}
        <div className="settings-actions">
          <button type="submit" className="primary-button settings-save-btn" disabled={saving}>
            {saving ? <Loader2 size={18} className="spin" /> : <Save size={18} />}
            <span>{saving ? "Saving preferences..." : "Save settings"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
